from __future__ import annotations

from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class RunnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: int
    horse_name: str
    age: int | None = None
    sex: str | None = None
    weight_kg: float | None = None
    draw: int | None = None
    handicap_value: float | None = None
    record_km_seconds: float | None = None
    ferrure: str | None = None
    equipment: str | None = None
    jockey_driver: str | None = None
    trainer: str | None = None
    recent_form: str | None = None
    scratched: bool


class RaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    scheduled_at: datetime
    discipline: str
    distance_m: int | None
    surface: str | None
    going: str | None
    class_name: str | None
    start_type: str | None
    status: str
    runners: list[RunnerOut] = []


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    race_date: date
    code: str
    track: str
    country: str | None
    races: list[RaceOut] = []


class ScoreOut(BaseModel):
    number: int
    horse_name: str
    performance: float
    placed: float
    hidden_potential: float
    robustness: float
    uncertainty: float
    line_strength: float
    reasons: list[str]
    breakdown: dict[str, Any]


class AnalysisOut(BaseModel):
    snapshot_id: int
    race_id: int
    generated_at: datetime
    methodology_version: str
    locked: bool
    confirmation: str
    summary: dict[str, Any]
    scores: list[ScoreOut]
