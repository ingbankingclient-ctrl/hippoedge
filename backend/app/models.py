from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (UniqueConstraint("race_date", "code", "track", name="uq_meeting"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    race_date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)
    track: Mapped[str] = mapped_column(String(120), index=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    races: Mapped[list["Race"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class Race(Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("meeting_id", "code", name="uq_race"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(180))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    discipline: Mapped[str] = mapped_column(String(64), index=True)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    surface: Mapped[str | None] = mapped_column(String(64), nullable=True)
    going: Mapped[str | None] = mapped_column(String(64), nullable=True)
    class_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purse_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="scheduled", index=True)
    source_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    meeting: Mapped[Meeting] = relationship(back_populates="races")
    runners: Mapped[list["Runner"]] = relationship(back_populates="race", cascade="all, delete-orphan")
    snapshots: Mapped[list["AnalysisSnapshot"]] = relationship(back_populates="race", cascade="all, delete-orphan")
    result: Mapped["RaceResult | None"] = relationship(back_populates="race", cascade="all, delete-orphan", uselist=False)


class Runner(Base):
    __tablename__ = "runners"
    __table_args__ = (UniqueConstraint("race_id", "number", name="uq_runner"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    horse_name: Mapped[str] = mapped_column(String(160), index=True)
    horse_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(24), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    draw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    handicap_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    earnings_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    record_km_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ferrure: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jockey_driver: Mapped[str | None] = mapped_column(String(120), nullable=True)
    trainer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    recent_form: Mapped[str | None] = mapped_column(String(120), nullable=True)
    scratched: Mapped[bool] = mapped_column(Boolean, default=False)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    race: Mapped[Race] = relationship(back_populates="runners")
    history: Mapped[list["HorseHistory"]] = relationship(back_populates="runner", cascade="all, delete-orphan")


class HorseHistory(Base):
    __tablename__ = "horse_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id", ondelete="CASCADE"), index=True)
    race_date: Mapped[date] = mapped_column(Date, index=True)
    track: Mapped[str | None] = mapped_column(String(120), nullable=True)
    race_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    discipline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    going: Mapped[str | None] = mapped_column(String(64), nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disqualified: Mapped[bool] = mapped_column(Boolean, default=False)
    chrono_km_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    class_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    draw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(160), nullable=True)
    field_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    margin_to_winner: Mapped[float | None] = mapped_column(Float, nullable=True)
    opponents: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    runner: Mapped[Runner] = relationship(back_populates="history")


class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id", ondelete="CASCADE"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    methodology_version: Mapped[str] = mapped_column(String(64))
    data_hash: Mapped[str] = mapped_column(String(64), index=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    race: Mapped[Race] = relationship(back_populates="snapshots")
    scores: Mapped[list["RunnerScore"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")


class RunnerScore(Base):
    __tablename__ = "runner_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("analysis_snapshots.id", ondelete="CASCADE"), index=True)
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id", ondelete="CASCADE"), index=True)
    performance: Mapped[float] = mapped_column(Float)
    placed: Mapped[float] = mapped_column(Float)
    hidden_potential: Mapped[float] = mapped_column(Float)
    robustness: Mapped[float] = mapped_column(Float)
    uncertainty: Mapped[float] = mapped_column(Float)
    line_strength: Mapped[float] = mapped_column(Float)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    snapshot: Mapped[AnalysisSnapshot] = relationship(back_populates="scores")
    runner: Mapped[Runner] = relationship()


class RaceResult(Base):
    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id", ondelete="CASCADE"), unique=True, index=True)
    official_order: Mapped[list[int]] = mapped_column(JSON, default=list)
    non_finishers: Mapped[list[int]] = mapped_column(JSON, default=list)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    race: Mapped[Race] = relationship(back_populates="result")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("analysis_snapshots.id", ondelete="CASCADE"), unique=True, index=True)
    winner_hit_top3: Mapped[bool] = mapped_column(Boolean, default=False)
    podium_coverage: Mapped[int] = mapped_column(Integer, default=0)
    placed_pick_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    winning_pick_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
