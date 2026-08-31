from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from typing import Any, Iterable


FORBIDDEN_MARKET_OR_OPINION_KEYS = {
    "cote", "cotes", "odds", "favori", "favorite", "popularite", "popularité",
    "note_ia", "note ia", "cote_bzh", "value_bet", "value-bet", "pronostic",
    "pronostics", "selection", "sélection", "avis", "conseil", "tips", "tip",
    "elo_cheval", "classement", "rank_prediction",
}


def sanitize_objective_payload(value: Any) -> Any:
    """Recursively removes market, popularity and editorial/prediction fields.

    This is deliberately conservative. It is the hard firewall that preserves the
    user's independence requirement even when a provider response mixes raw facts
    with odds or editorial rankings.
    """
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            normalized = str(k).strip().lower().replace("_", " ")
            compact = str(k).strip().lower()
            if normalized in FORBIDDEN_MARKET_OR_OPINION_KEYS or compact in FORBIDDEN_MARKET_OR_OPINION_KEYS:
                continue
            if any(token in normalized for token in ("pronostic", "cote bzh", "note ia", "popularit", "favori", "value bet")):
                continue
            out[k] = sanitize_objective_payload(v)
        return out
    if isinstance(value, list):
        return [sanitize_objective_payload(x) for x in value]
    return value


def parse_record_to_seconds(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if 50 <= v <= 150:
            return v
    s = str(value).strip().lower().replace('"', "").replace("’", "'")
    # 1'13"5 / 1:13.5 / 73.5
    m = re.search(r"(?:(\d+)\s*[':])?\s*(\d{1,2})(?:[\.,](\d))?", s)
    if not m:
        return None
    minutes = int(m.group(1) or 0)
    seconds = int(m.group(2))
    tenth = int(m.group(3) or 0)
    total = minutes * 60 + seconds + tenth / 10
    return total if 50 <= total <= 150 else None


def to_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except Exception:
        return None


def to_int(value: Any) -> int | None:
    f = to_float(value)
    return int(f) if f is not None else None


def clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def mean(values: Iterable[float]) -> float | None:
    vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return sum(vals) / len(vals) if vals else None


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_iso_or_local(date_str: str, time_str: str | None) -> datetime:
    t = (time_str or "12:00").strip().replace("h", ":")
    if len(t) == 5 and ":" in t:
        return datetime.fromisoformat(f"{date_str}T{t}:00")
    if len(t) == 8:
        return datetime.fromisoformat(f"{date_str}T{t}")
    return datetime.fromisoformat(f"{date_str}T12:00:00")
