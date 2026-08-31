from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .models import AnalysisSnapshot, Evaluation, Race, RunnerScore
from .scoring import score_race
from .utils import stable_hash

CONFIRMATION = (
    "Je confirme que le moteur n'utilise volontairement ni classements, ni pronostics, ni favoris, "
    "ni cotes, ni popularité, ni avis éditoriaux. La liste des partants provient de la fiche de course "
    "et les scores sont construits uniquement à partir des données objectives de course et de performance disponibles."
)


def load_race(db: Session, race_id: int) -> Race | None:
    return db.scalar(
        select(Race).where(Race.id==race_id).options(
            selectinload(Race.meeting),
            selectinload(Race.runners).selectinload(__import__('app.models', fromlist=['Runner']).Runner.history),
            selectinload(Race.snapshots).selectinload(AnalysisSnapshot.scores),
        )
    )


def generate_analysis(db: Session, race: Race, lock: bool = False) -> AnalysisSnapshot:
    settings=get_settings()
    data_fingerprint={
        "race": {"id":race.id,"going":race.going,"distance":race.distance_m,"discipline":race.discipline,"start":race.start_type},
        "runners": [
            {"n":r.number,"name":r.horse_name,"scratched":r.scratched,"weight":r.weight_kg,"draw":r.draw,"ferrure":r.ferrure,"equipment":r.equipment,
             "history":[{"d":h.race_date.isoformat(),"p":h.position,"dq":h.disqualified,"t":h.chrono_km_seconds,"track":h.track,"dist":h.distance_m,"class":h.class_name} for h in r.history]}
            for r in race.runners
        ]
    }
    dh=stable_hash(data_fingerprint)
    latest=max(race.snapshots,key=lambda x:x.generated_at) if race.snapshots else None
    if latest and latest.data_hash==dh and not lock:
        return latest
    cards=score_race(race,race.runners)
    snap=AnalysisSnapshot(race_id=race.id, methodology_version=settings.methodology_version, data_hash=dh, locked=lock, locked_at=datetime.utcnow() if lock else None)
    db.add(snap); db.flush()
    scores=[]
    for r in race.runners:
        if r.scratched or r.id not in cards: continue
        c=cards[r.id]
        rs=RunnerScore(snapshot_id=snap.id,runner_id=r.id,performance=c.performance,placed=c.placed,hidden_potential=c.hidden_potential,robustness=c.robustness,uncertainty=c.uncertainty,line_strength=c.line_strength,reasons=c.reasons,breakdown=c.breakdown)
        db.add(rs); scores.append((r,rs))
    perf=sorted(scores,key=lambda x:x[1].performance,reverse=True)
    placed=sorted(scores,key=lambda x:x[1].placed,reverse=True)
    hidden=sorted(scores,key=lambda x:x[1].hidden_potential,reverse=True)
    convergence=sorted(scores,key=lambda x:(x[1].performance+x[1].placed)/2,reverse=True)
    snap.summary={
        "top3_performance":[x[0].number for x in perf[:3]],
        "top3_placed":[x[0].number for x in placed[:3]],
        "winning_pick":perf[0][0].number if perf else None,
        "placed_pick":placed[0][0].number if placed else None,
        "hidden_potential":[x[0].number for x in hidden[:2]],
        "best_convergence":[x[0].number for x in convergence[:3]],
        "selection_8":[x[0].number for x in convergence[:8]],
        "method_notes":[
            "Les lignes indirectes restent un bonus de confirmation et ne dominent jamais la performance propre.",
            "Une faute récente réduit surtout la sécurité au trot ; elle n'efface pas automatiquement la valeur précédente.",
            "La régularité sur 2-3 sorties est plafonnée par l'incertitude d'échantillon.",
            "Le numéro de corde/autostart n'est pas traité comme un bonus automatique hors contexte.",
        ]
    }
    db.commit(); db.refresh(snap)
    return snap


def lock_latest_snapshot(db: Session, race: Race) -> AnalysisSnapshot:
    latest=max(race.snapshots,key=lambda x:x.generated_at) if race.snapshots else generate_analysis(db,race)
    if latest.locked: return latest
    latest.locked=True; latest.locked_at=datetime.utcnow(); db.commit(); db.refresh(latest); return latest


def evaluate_locked_snapshots(db: Session, race: Race):
    if not race.result or not race.result.official_order: return
    podium=race.result.official_order[:3]
    winner=podium[0] if podium else None
    for snap in [s for s in race.snapshots if s.locked]:
        if db.scalar(select(Evaluation).where(Evaluation.snapshot_id==snap.id)): continue
        summary=snap.summary or {}
        top3=summary.get("top3_performance",[])
        pick=summary.get("winning_pick")
        ppick=summary.get("placed_pick")
        ev=Evaluation(snapshot_id=snap.id,winner_hit_top3=winner in top3 if winner else False,podium_coverage=sum(1 for x in podium if x in top3),winning_pick_hit=pick==winner,placed_pick_hit=ppick in podium,
                      details={"official_podium":podium,"top3_performance":top3,"top3_placed":summary.get("top3_placed",[]),"winning_pick":pick,"placed_pick":ppick})
        db.add(ev)
    db.commit()
