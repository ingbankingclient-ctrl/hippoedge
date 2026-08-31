from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Meeting, Race, Runner, HorseHistory, RaceResult, Evaluation
from .providers.base import RacingProvider
from .utils import parse_iso_or_local, parse_record_to_seconds, sanitize_objective_payload, to_float, to_int


def _first(d: dict, keys: Iterable[str], default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _normalize_discipline(value: str | None) -> str:
    x = (value or "").strip().lower()
    if "mont" in x: return "Trot monté"
    if "attel" in x or x == "trot": return "Trot attelé"
    if "haie" in x: return "Haies"
    if "steeple" in x: return "Steeple-chase"
    if "cross" in x: return "Cross"
    if "plat" in x or "galop" in x: return "Plat"
    return value or "Inconnue"


def _program_meetings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", payload)
    for key in ("reunions", "réunions", "meetings"):
        if isinstance(data, dict) and isinstance(data.get(key), list):
            return data[key]
    # Some APIs flatten courses; group later.
    courses = data.get("courses") if isinstance(data, dict) else None
    if isinstance(courses, list):
        groups: dict[tuple[str,str], dict] = {}
        for c in courses:
            code = str(_first(c, ["reunion", "code_reunion", "meeting"], "R?"))
            track = str(_first(c, ["hippodrome", "track", "lieu"], "Inconnu"))
            groups.setdefault((code,track), {"code":code,"hippodrome":track,"courses":[]})["courses"].append(c)
        return list(groups.values())
    return []


def _meeting_courses(m: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("courses", "races"):
        if isinstance(m.get(key), list): return m[key]
    return []


def _runner_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", payload)
    for key in ("partants", "runners", "participants"):
        if isinstance(data, dict) and isinstance(data.get(key), list): return data[key]
    return []


def _history_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", payload)
    if isinstance(data, list): return data
    if isinstance(data, dict):
        for key in ("historique", "history", "courses", "performances"):
            if isinstance(data.get(key), list): return data[key]
    return []


def _parse_position(v: Any) -> tuple[int | None, bool]:
    if v is None: return None, False
    s = str(v).strip().lower()
    dq = any(x in s for x in ("dai", "da", "dm", "dq", "disq", "dist"))
    m = re.search(r"\d+", s)
    return (int(m.group()) if m else None), dq


class ImportService:
    def __init__(self, provider: RacingProvider):
        self.provider = provider

    async def import_day(self, db: Session, day: date, enrich_history: bool = True) -> list[Meeting]:
        payload = sanitize_objective_payload(await self.provider.get_program(day))
        meetings: list[Meeting] = []
        for mraw in _program_meetings(payload):
            mcode = str(_first(mraw, ["code", "code_reunion", "reunion"], "R?"))
            track = str(_first(mraw, ["hippodrome", "track", "lieu", "name"], "Inconnu"))
            meeting = db.scalar(select(Meeting).where(Meeting.race_date==day, Meeting.code==mcode, Meeting.track==track))
            if not meeting:
                meeting = Meeting(race_date=day, code=mcode, track=track, country=_first(mraw,["pays","country"]), source=self.provider.name)
                db.add(meeting); db.flush()
            meetings.append(meeting)
            for craw in _meeting_courses(mraw):
                rcode = str(_first(craw,["code_course","code","rc"], ""))
                if not rcode:
                    # derive Cn from index if needed
                    rcode = f"{mcode}C{len(meeting.races)+1}"
                scheduled = parse_iso_or_local(day.isoformat(), str(_first(craw,["heure","heure_depart","time"],"12:00")))
                race = db.scalar(select(Race).where(Race.meeting_id==meeting.id, Race.code==rcode))
                if not race:
                    race = Race(meeting_id=meeting.id, code=rcode, name=str(_first(craw,["prix","name","nom"],rcode)), scheduled_at=scheduled,
                                discipline=_normalize_discipline(_first(craw,["discipline","specialite","type"])), distance_m=to_int(_first(craw,["distance","distance_m"])),
                                surface=_first(craw,["surface"]), going=_first(craw,["terrain","going"]), class_name=_first(craw,["classe","class","categorie"]),
                                purse_eur=to_int(_first(craw,["allocation","montant","purse"])), start_type=_first(craw,["depart","start_type","mode_depart"]),
                                source_ref=_first(craw,["url","source_ref"]), raw=sanitize_objective_payload(craw))
                    db.add(race); db.flush()
                else:
                    race.scheduled_at=scheduled; race.going=_first(craw,["terrain","going"],race.going); race.raw=sanitize_objective_payload(craw)
                # Fetch exact runners from race endpoint rather than trusting program summaries.
                try:
                    rp = sanitize_objective_payload(await self.provider.get_race(day, rcode, track))
                    await self._upsert_runners(db, race, rp, enrich_history)
                except Exception as e:
                    race.raw = {**(race.raw or {}), "runner_import_warning": str(e)}
        db.commit()
        return meetings

    async def _upsert_runners(self, db: Session, race: Race, payload: dict[str,Any], enrich_history: bool):
        for p in _runner_list(payload):
            num = to_int(_first(p,["num","numero","number"]))
            name = str(_first(p,["name","cheval","nom"], "")).strip()
            if not num or not name: continue
            runner = db.scalar(select(Runner).where(Runner.race_id==race.id, Runner.number==num))
            if not runner:
                runner=Runner(race_id=race.id, number=num, horse_name=name)
                db.add(runner); db.flush()
            runner.horse_name=name
            runner.horse_external_id=str(_first(p,["idcheval","horse_id","id_cheval"], runner.horse_external_id or "")) or None
            runner.age=to_int(_first(p,["age"],runner.age)); runner.sex=_first(p,["sexe","sex","sa"],runner.sex)
            runner.weight_kg=to_float(_first(p,["poids","weight","poids_kg"],runner.weight_kg)); runner.draw=to_int(_first(p,["corde","draw"],runner.draw))
            runner.handicap_value=to_float(_first(p,["valeur","handicap_value"],runner.handicap_value)); runner.earnings_eur=to_float(_first(p,["gains","earnings"],runner.earnings_eur))
            runner.record_km_seconds=parse_record_to_seconds(_first(p,["record","reduction_km","record_km"],runner.record_km_seconds)) or runner.record_km_seconds
            runner.ferrure=_first(p,["ferrure","fer"],runner.ferrure); runner.equipment=_first(p,["equipement","equipment","oeilleres"],runner.equipment)
            runner.start_position=to_int(_first(p,["position_depart","autostart","numero_autostart"], runner.start_position))
            runner.distance_m=to_int(_first(p,["distance","distance_m"],runner.distance_m)); runner.jockey_driver=_first(p,["jockey_driver","driver","jockey"],runner.jockey_driver)
            runner.trainer=_first(p,["entraineur","trainer"],runner.trainer); runner.recent_form=str(_first(p,["musique","form"],runner.recent_form or "")) or None
            runner.scratched=bool(_first(p,["np","non_partant","scratched"],False)); runner.raw=sanitize_objective_payload(p)
            if enrich_history and runner.horse_external_id:
                try:
                    hp = sanitize_objective_payload(await self.provider.get_horse_history(runner.horse_external_id, race.discipline))
                    self._replace_history(db, runner, hp)
                except Exception as e:
                    runner.raw={**(runner.raw or {}),"history_warning":str(e)}
        db.flush()

    def _replace_history(self, db: Session, runner: Runner, payload: dict[str,Any]):
        # Keep current rows if provider sends no data.
        rows=_history_list(payload)
        if not rows: return
        for old in list(runner.history): db.delete(old)
        db.flush()
        for h in rows[:50]:
            ds=str(_first(h,["date","date_course","race_date"],""))[:10]
            try: d=date.fromisoformat(ds)
            except Exception: continue
            pos,dq=_parse_position(_first(h,["position","rang","rank","arrivee"]))
            dq=bool(_first(h,["disqualifie","disqualified"],dq))
            item=HorseHistory(runner_id=runner.id, race_date=d, track=_first(h,["hippodrome","track","lieu"]), race_code=_first(h,["code_course","race_code"]),
                              discipline=_normalize_discipline(_first(h,["discipline","specialite"])), distance_m=to_int(_first(h,["distance","distance_m"])), going=_first(h,["terrain","going"]),
                              position=pos, disqualified=dq, chrono_km_seconds=parse_record_to_seconds(_first(h,["reduction_km","chrono_km","record"])), class_name=_first(h,["classe","class","categorie"]),
                              weight_kg=to_float(_first(h,["poids","weight"])), draw=to_int(_first(h,["corde","draw"])), start_type=_first(h,["depart","start_type"]),
                              equipment=_first(h,["ferrure","fer","equipement","equipment"]), field_size=to_int(_first(h,["nb_partants","field_size"])),
                              margin_to_winner=to_float(_first(h,["ecart_gagnant","margin_to_winner"])), opponents=_first(h,["adversaires","opponents"],[]) or [], raw=sanitize_objective_payload(h))
            db.add(item)

    async def import_results(self, db: Session, day: date):
        payload=sanitize_objective_payload(await self.provider.get_results(day))
        data=payload.get("data",payload)
        results=data.get("results",[]) if isinstance(data,dict) else []
        for rr in results:
            code=str(_first(rr,["code_course","code","rc"],"")); track=str(_first(rr,["hippodrome","track"],""))
            race=db.scalar(select(Race).join(Meeting).where(Meeting.race_date==day, Race.code==code, Meeting.track.ilike(f"%{track}%"))) if track else db.scalar(select(Race).join(Meeting).where(Meeting.race_date==day,Race.code==code))
            if not race: continue
            arrival=_first(rr,["arrivee","arrival"],[]) or []
            order=[]
            for x in arrival:
                if isinstance(x,dict):
                    n=to_int(_first(x,["numero","num","number"])); rank=to_int(_first(x,["rank","rang"]));
                    if n and (rank or 99)>0: order.append((rank or 99,n))
                else:
                    n=to_int(x)
                    if n: order.append((len(order)+1,n))
            order=[n for _,n in sorted(order)]
            non_finishers=[to_int(x) for x in (_first(rr,["non_classes","non_finishers"],[]) or [])]
            non_finishers=[x for x in non_finishers if x]
            if not race.result: race.result=RaceResult(official_order=order,non_finishers=non_finishers,raw=rr)
            else: race.result.official_order=order; race.result.non_finishers=non_finishers; race.result.raw=rr
            race.status="finished"
        db.commit()
