from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .analysis_service import CONFIRMATION, evaluate_locked_snapshots, generate_analysis, lock_latest_snapshot
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .importer import ImportService
from .models import AnalysisSnapshot, Evaluation, Meeting, Race, Runner, RunnerScore
from .providers import DemoProvider, TurfBzhProvider
from .schemas import AnalysisOut, MeetingOut, ScoreOut

settings=get_settings()


def provider_factory():
    if settings.provider.lower()=="turfbzh":
        return TurfBzhProvider(settings.turfbzh_base_url, settings.turfbzh_api_key)
    return DemoProvider()


async def maintenance_loop(stop: asyncio.Event):
    provider=provider_factory(); importer=ImportService(provider)
    while not stop.is_set():
        db=SessionLocal()
        try:
            today=date.today(); tomorrow=today+timedelta(days=1)
            # J+1 is the product's main promise; current day is refreshed for NP/results.
            for d in (today,tomorrow):
                try: await importer.import_day(db,d,enrich_history=True)
                except Exception as e: print("refresh warning",d,e)
            try: await importer.import_results(db,today)
            except Exception as e: print("results warning",e)
            races=db.scalars(select(Race).options(selectinload(Race.runners).selectinload(Runner.history),selectinload(Race.meeting),selectinload(Race.snapshots))).all()
            now=datetime.now()
            for race in races:
                if race.status=="finished":
                    evaluate_locked_snapshots(db,race); continue
                # Generate J+1/current snapshots and freeze a pre-race record shortly before off time.
                try: generate_analysis(db,race)
                except Exception as e: print("analysis warning",race.id,e)
                if race.scheduled_at <= now + timedelta(minutes=settings.auto_lock_minutes_before):
                    try: lock_latest_snapshot(db,race)
                    except Exception as e: print("lock warning",race.id,e)
        finally:
            db.close()
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.refresh_seconds)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    stop=asyncio.Event(); task=asyncio.create_task(maintenance_loop(stop))
    app.state.stop=stop; app.state.task=task
    yield
    stop.set(); task.cancel()
    try: await task
    except BaseException: pass


app=FastAPI(title=settings.app_name,version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_credentials=False,allow_methods=["*"],allow_headers=["*"])


@app.get("/health")
def health():
    return {"ok":True,"app":settings.app_name,"provider":settings.provider,"methodology":settings.methodology_version,"independence_firewall":True}


@app.post("/api/refresh")
async def refresh(day: date=Query(default_factory=date.today), db: Session=Depends(get_db)):
    importer=ImportService(provider_factory())
    meetings=await importer.import_day(db,day,enrich_history=True)
    for meeting in meetings:
        for race in meeting.races:
            generate_analysis(db,race)
    return {"ok":True,"date":day,"meetings":len(meetings)}


@app.get("/api/program/{day}",response_model=list[MeetingOut])
def program(day: date, db: Session=Depends(get_db)):
    rows=db.scalars(select(Meeting).where(Meeting.race_date==day).options(selectinload(Meeting.races).selectinload(Race.runners)).order_by(Meeting.code)).all()
    return rows


@app.get("/api/tomorrow",response_model=list[MeetingOut])
def tomorrow(db: Session=Depends(get_db)):
    day=date.today()+timedelta(days=1)
    return program(day,db)


@app.get("/api/races/{race_id}/analysis",response_model=AnalysisOut)
def analysis(race_id:int, force:bool=False, db: Session=Depends(get_db)):
    race=db.scalar(select(Race).where(Race.id==race_id).options(selectinload(Race.meeting),selectinload(Race.runners).selectinload(Runner.history),selectinload(Race.snapshots).selectinload(AnalysisSnapshot.scores)))
    if not race: raise HTTPException(404,"Course introuvable")
    snap=generate_analysis(db,race) if force or not race.snapshots else max(race.snapshots,key=lambda x:x.generated_at)
    scores=db.scalars(select(RunnerScore).where(RunnerScore.snapshot_id==snap.id).options(selectinload(RunnerScore.runner))).all()
    return AnalysisOut(snapshot_id=snap.id,race_id=race.id,generated_at=snap.generated_at,methodology_version=snap.methodology_version,locked=snap.locked,confirmation=CONFIRMATION,summary=snap.summary,
                       scores=[ScoreOut(number=s.runner.number,horse_name=s.runner.horse_name,performance=s.performance,placed=s.placed,hidden_potential=s.hidden_potential,robustness=s.robustness,uncertainty=s.uncertainty,line_strength=s.line_strength,reasons=s.reasons,breakdown=s.breakdown) for s in sorted(scores,key=lambda x:x.performance,reverse=True)])


@app.post("/api/races/{race_id}/lock")
def lock(race_id:int, db:Session=Depends(get_db)):
    race=db.scalar(select(Race).where(Race.id==race_id).options(selectinload(Race.runners).selectinload(Runner.history),selectinload(Race.meeting),selectinload(Race.snapshots)))
    if not race: raise HTTPException(404,"Course introuvable")
    snap=lock_latest_snapshot(db,race)
    return {"ok":True,"snapshot_id":snap.id,"locked_at":snap.locked_at,"message":"Analyse pré-course figée : elle ne sera pas réécrite après l'arrivée."}


@app.get("/api/stats")
def stats(db:Session=Depends(get_db)):
    evs=db.scalars(select(Evaluation)).all(); n=len(evs)
    if not n: return {"races_evaluees":0,"message":"Les statistiques apparaîtront après les premières arrivées avec snapshots verrouillés."}
    return {
        "races_evaluees":n,
        "choix_gagnant_pct":round(sum(e.winning_pick_hit for e in evs)/n*100,1),
        "choix_place_top3_pct":round(sum(e.placed_pick_hit for e in evs)/n*100,1),
        "gagnant_dans_top3_performance_pct":round(sum(e.winner_hit_top3 for e in evs)/n*100,1),
        "couverture_podium_moyenne_sur_3":round(sum(e.podium_coverage for e in evs)/n,2),
    }
