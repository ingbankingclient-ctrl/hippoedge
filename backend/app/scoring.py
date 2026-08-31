from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import median
from typing import Iterable
import math

from .models import HorseHistory, Race, Runner
from .utils import clip, mean


@dataclass
class ScoreCard:
    performance: float
    placed: float
    hidden_potential: float
    robustness: float
    uncertainty: float
    line_strength: float
    reasons: list[str]
    breakdown: dict


POSITION_POINTS = {1: 100, 2: 91, 3: 84, 4: 77, 5: 70, 6: 62, 7: 55, 8: 48, 9: 42, 10: 36}


def _position_score(h: HorseHistory) -> float:
    if h.disqualified:
        return 16.0
    if h.position is None:
        return 35.0
    return float(POSITION_POINTS.get(h.position, max(18, 36 - (h.position - 10) * 2)))


def _recency_weights(n: int) -> list[float]:
    base = [1.00, .88, .77, .67, .58, .50, .43, .37, .32, .28]
    return base[:n] + [0.24] * max(0, n-len(base))


def weighted_form(history: list[HorseHistory]) -> float:
    recent = sorted(history, key=lambda h: h.race_date, reverse=True)[:10]
    if not recent:
        return 50.0
    weights = _recency_weights(len(recent))
    vals = [_position_score(h) for h in recent]
    return sum(v*w for v, w in zip(vals, weights)) / sum(weights)


def consistency_score(history: list[HorseHistory]) -> float:
    recent = sorted(history, key=lambda h: h.race_date, reverse=True)[:10]
    completed = [h for h in recent if not h.disqualified and h.position is not None]
    if not recent:
        return 45.0
    dq_rate = sum(1 for h in recent if h.disqualified) / len(recent)
    top5_rate = sum(1 for h in completed if h.position <= 5) / max(1, len(completed))
    top3_rate = sum(1 for h in completed if h.position <= 3) / max(1, len(completed))
    return clip(42 + top5_rate*30 + top3_rate*20 - dq_rate*36)


def progression_score(history: list[HorseHistory]) -> float:
    recent = sorted(history, key=lambda h: h.race_date, reverse=True)[:5]
    if len(recent) < 2:
        return 50.0
    vals = [_position_score(h) for h in reversed(recent)]  # old -> recent
    diffs = [b-a for a,b in zip(vals, vals[1:])]
    avg = mean(diffs) or 0
    return clip(50 + avg * 1.8)


def aptitude_score(race: Race, history: list[HorseHistory]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if not history:
        return 50.0, reasons
    scores = []
    for h in history:
        s = _position_score(h)
        weight = 0.0
        if race.distance_m and h.distance_m:
            d = abs(race.distance_m - h.distance_m)
            if d <= 150: weight += 1.8
            elif d <= 400: weight += 1.0
        if h.track and race.meeting and h.track.lower() == race.meeting.track.lower():
            weight += 2.0
        if race.going and h.going and race.going.lower() in h.going.lower() or (h.going and race.going and h.going.lower() in race.going.lower()):
            weight += 1.1
        if race.discipline and h.discipline and _discipline_family(race.discipline) == _discipline_family(h.discipline):
            weight += 1.2
        if weight:
            scores.append((s, weight))
    if not scores:
        return 50.0, reasons
    total = sum(s*w for s,w in scores)/sum(w for _,w in scores)
    if any((h.track or '').lower() == (race.meeting.track or '').lower() and not h.disqualified and (h.position or 99) <= 3 for h in history):
        reasons.append("Référence placée sur l'hippodrome")
    if race.distance_m and any(h.distance_m and abs(h.distance_m-race.distance_m)<=150 and not h.disqualified and (h.position or 99)<=3 for h in history):
        reasons.append("Référence placée sur une distance très proche")
    return clip(total), reasons


def _discipline_family(d: str | None) -> str:
    x = (d or '').lower()
    if 'mont' in x: return 'trot_monte'
    if 'attel' in x or 'trot' in x: return 'trot_attele'
    if any(k in x for k in ('haie','steeple','obstacle','cross')): return 'obstacle'
    return 'galop'


def speed_score(race: Race, runner: Runner, history: list[HorseHistory], field_histories: Iterable[list[HorseHistory]]) -> float:
    if _discipline_family(race.discipline) not in ('trot_attele','trot_monte'):
        # Gallop timing data are provider-dependent. Use margins if available, otherwise neutral.
        margins = [h.margin_to_winner for h in history[:8] if h.margin_to_winner is not None and not h.disqualified]
        if not margins:
            return 52.0
        m = mean(margins) or 0
        return clip(82 - m*6, 25, 95)

    own = [h.chrono_km_seconds for h in history[:10] if h.chrono_km_seconds and not h.disqualified]
    if runner.record_km_seconds:
        own.append(runner.record_km_seconds)
    all_times = [h.chrono_km_seconds for hs in field_histories for h in hs[:10] if h.chrono_km_seconds and not h.disqualified]
    if not own or not all_times:
        return 50.0
    own_best = min(own)
    med = median(all_times)
    # 1 second/km around the field median is meaningful at trot.
    return clip(68 + (med-own_best)*9, 25, 97)


def dq_risk(history: list[HorseHistory]) -> float:
    recent = sorted(history, key=lambda h: h.race_date, reverse=True)[:8]
    if not recent:
        return 35.0
    rate = sum(1 for h in recent if h.disqualified)/len(recent)
    last = recent[0].disqualified
    return clip(rate*85 + (12 if last else 0), 0, 95)


def sample_uncertainty(history: list[HorseHistory], runner: Runner) -> float:
    n = len(history)
    score = 65 if n <= 2 else 52 if n <= 4 else 36 if n <= 7 else 22
    score += dq_risk(history)*0.25
    if history:
        days = (date.today() - max(h.race_date for h in history)).days
        if days > 240: score += 22
        elif days > 120: score += 12
    if runner.age and runner.age <= 3 and n <= 4:
        score += 10
    return clip(score)


def scenario_robustness(race: Race, runner: Runner, history: list[HorseHistory]) -> float:
    cons = consistency_score(history)
    risk = dq_risk(history)
    n = len(history)
    experience = clip(35 + min(n, 15)*4)
    start = 50.0
    fam = _discipline_family(race.discipline)
    if fam == 'trot_attele' and race.start_type and 'auto' in race.start_type.lower():
        # Good number is only a meaningful bonus when there's actual autostart experience.
        auto_hist = [h for h in history if h.start_type and 'auto' in h.start_type.lower()]
        if runner.start_position and auto_hist:
            if 2 <= runner.start_position <= 5: start = 72
            elif runner.start_position in (1,6): start = 62
            else: start = 48
        elif runner.start_position:
            start = 54
    elif fam == 'galop' and runner.draw:
        # Avoid blind draw dogma; keep effect modest without contextual bias data.
        start = 58 if runner.draw <= 5 else 52
    return clip(cons*0.43 + (100-risk)*0.27 + experience*0.20 + start*0.10)


def class_score(race: Race, history: list[HorseHistory]) -> float:
    def rank(s: str | None) -> int:
        x = (s or '').lower()
        if 'groupe 1' in x or 'group 1' in x: return 100
        if 'groupe 2' in x or 'group 2' in x: return 95
        if 'groupe 3' in x or 'group 3' in x: return 90
        if 'listed' in x: return 86
        if 'course a' in x or 'classe 1' in x: return 82
        if 'course b' in x or 'classe 2' in x: return 76
        if 'course c' in x: return 70
        if 'course d' in x or 'classe 3' in x: return 64
        if 'course e' in x: return 58
        if 'course f' in x: return 52
        if 'handicap' in x: return 62
        return 55
    target = rank(race.class_name)
    vals = []
    for h in history[:10]:
        hclass = rank(h.class_name)
        pos = _position_score(h)
        vals.append(50 + (hclass-target)*0.65 + (pos-50)*0.35)
    return clip(mean(vals) if vals else 50)


def weight_and_draw_score(race: Race, runner: Runner, field: list[Runner]) -> float:
    fam = _discipline_family(race.discipline)
    score = 50.0
    weights = [r.weight_kg for r in field if r.weight_kg is not None and not r.scratched]
    if runner.weight_kg is not None and weights:
        lo, hi = min(weights), max(weights)
        if hi > lo:
            score += ((hi-runner.weight_kg)/(hi-lo)-0.5)*24
    if fam == 'galop' and runner.draw is not None:
        # Small contribution only; actual draw bias should be learned from same-day/historical context.
        n = max(1, len(field))
        if runner.draw <= max(3, n//3): score += 5
        elif runner.draw >= max(8, int(n*.8)): score -= 3
    if fam == 'trot_attele' and race.start_type and 'auto' in race.start_type.lower() and runner.start_position:
        if 2 <= runner.start_position <= 5: score += 8
        elif runner.start_position >= 8: score -= 5
    return clip(score)


def hidden_potential_score(race: Race, runner: Runner, history: list[HorseHistory], field: list[Runner]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if not history:
        base = 52.0
    else:
        recent = sorted(history, key=lambda h: h.race_date, reverse=True)
        recent3 = recent[:3]
        older = recent[3:10]
        recent_avg = mean([_position_score(h) for h in recent3]) or 50
        old_best = max([_position_score(h) for h in older], default=recent_avg)
        masked = max(0, old_best - recent_avg)
        base = 50 + masked*0.65
        if masked >= 18:
            reasons.append("Ancienne valeur nettement supérieure à la forme récente")
        # DQ masks performance, but is not a performance failure.
        if recent3 and recent3[0].disqualified and any(not h.disqualified and _position_score(h)>=82 for h in recent[1:5]):
            base += 10
            reasons.append("Faute récente après une performance propre de haut niveau")
    wd = weight_and_draw_score(race, runner, field)
    if wd >= 62:
        base += (wd-50)*0.45
        reasons.append("Configuration poids/position favorable")
    prog = progression_score(history)
    if prog >= 63:
        base += 7
        reasons.append("Courbe de progression récente")
    # Young/low-sample profiles have potential but also uncertainty. Don't turn it into a certainty.
    if runner.age and runner.age <= 4 and 2 <= len(history) <= 5:
        base += 4
        reasons.append("Faible historique : marge de progression encore ouverte")
    return clip(base), reasons


def line_strength_score(history: list[HorseHistory]) -> float:
    # Only objective opponent outcomes are accepted here. Provider editorial 'lines' are never used.
    vals = []
    for h in history[:8]:
        if not h.opponents:
            continue
        confirmed = 0
        total = 0
        for o in h.opponents:
            if not isinstance(o, dict):
                continue
            total += 1
            later_wins = int(o.get('later_wins') or 0)
            later_places = int(o.get('later_places') or 0)
            confirmed += min(2, later_wins*2 + later_places)
        if total:
            vals.append(50 + min(35, confirmed/total*10))
    return clip(mean(vals) if vals else 50)


def equipment_signal(runner: Runner, history: list[HorseHistory]) -> tuple[float, list[str]]:
    reasons = []
    current = (runner.ferrure or runner.equipment or '').strip().lower()
    if not current or not history:
        return 50, reasons
    same = [h for h in history if (h.equipment or '').strip().lower() == current]
    if not same:
        return 50, reasons
    score = mean([_position_score(h) for h in same]) or 50
    if score >= 75:
        reasons.append("Configuration du jour déjà associée à de bonnes performances")
    return clip(score), reasons


def score_race(race: Race, runners: list[Runner]) -> dict[int, ScoreCard]:
    active = [r for r in runners if not r.scratched]
    field_histories = [sorted(r.history, key=lambda h: h.race_date, reverse=True) for r in active]
    output: dict[int, ScoreCard] = {}

    for runner in active:
        hist = sorted(runner.history, key=lambda h: h.race_date, reverse=True)
        form = weighted_form(hist)
        cons = consistency_score(hist)
        prog = progression_score(hist)
        aptitude, apt_reasons = aptitude_score(race, hist)
        speed = speed_score(race, runner, hist, field_histories)
        cls = class_score(race, hist)
        wd = weight_and_draw_score(race, runner, active)
        hidden, hidden_reasons = hidden_potential_score(race, runner, hist, active)
        robust = scenario_robustness(race, runner, hist)
        uncertainty = sample_uncertainty(hist, runner)
        line = line_strength_score(hist)
        equip, eq_reasons = equipment_signal(runner, hist)
        risk = dq_risk(hist)

        fam = _discipline_family(race.discipline)
        # Core philosophy: own performance evidence dominates indirect lines.
        if fam in ('trot_attele','trot_monte'):
            performance = (
                form*.22 + speed*.20 + aptitude*.13 + cls*.12 + prog*.10 +
                hidden*.09 + cons*.06 + wd*.04 + equip*.025 + line*.015
            )
        else:
            performance = (
                form*.25 + aptitude*.17 + cls*.13 + prog*.11 + hidden*.11 +
                cons*.09 + wd*.07 + speed*.04 + equip*.015 + line*.015
            )
        # Placed score: consistency + technical cleanliness matter more, but never from 2-3 runs alone.
        sample_factor = min(1.0, len(hist)/7) if hist else 0.55
        effective_cons = 50 + (cons-50)*sample_factor
        placed = performance*.47 + effective_cons*.18 + robust*.18 + aptitude*.09 + (100-risk)*.08

        reasons = []
        if form >= 75: reasons.append("Forme récente solide")
        if cons >= 78: reasons.append("Régularité de fond")
        if prog >= 64: reasons.append("Progression récente mesurable")
        if speed >= 78: reasons.append("Capacité chronométrique supérieure au lot")
        if cls >= 72: reasons.append("A déjà tenu un niveau de course comparable ou supérieur")
        reasons.extend(apt_reasons + hidden_reasons + eq_reasons)
        if fam.startswith('trot') and risk >= 42:
            reasons.append("Risque de faute à intégrer dans la sécurité")
        if uncertainty >= 60:
            reasons.append("Profil volatil / peu documenté")
        if robust >= 82:
            reasons.append("Robuste à plusieurs scénarios de course")

        output[runner.id] = ScoreCard(
            performance=round(clip(performance), 1),
            placed=round(clip(placed), 1),
            hidden_potential=round(hidden, 1),
            robustness=round(robust, 1),
            uncertainty=round(uncertainty, 1),
            line_strength=round(line, 1),
            reasons=reasons[:8],
            breakdown={
                "form": round(form,1), "consistency": round(cons,1), "progression": round(prog,1),
                "aptitude": round(aptitude,1), "speed": round(speed,1), "class": round(cls,1),
                "weight_draw_start": round(wd,1), "equipment": round(equip,1), "dq_risk": round(risk,1),
                "sample_size": len(hist), "principle": "own_performance_over_indirect_lines",
            },
        )
    return output
