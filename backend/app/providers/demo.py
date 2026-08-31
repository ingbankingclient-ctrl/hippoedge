from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from .base import RacingProvider


class DemoProvider(RacingProvider):
    name = "demo"

    def _program(self, day: date) -> dict[str, Any]:
        return {
            "data": {
                "date": day.isoformat(),
                "reunions": [
                    {"code": "R1", "hippodrome": "Saint-Cloud", "pays": "France", "courses": [
                        {"code_course": "R1C1", "prix": "Prix Démo Galop", "heure": "13:55", "discipline": "Plat", "distance": 2400, "terrain": "Souple", "classe": "Handicap"},
                        {"code_course": "R1C2", "prix": "Prix Démo Obstacle", "heure": "14:30", "discipline": "Haies", "distance": 3600, "terrain": "Très souple", "classe": "Classe 2"},
                    ]},
                    {"code": "R4", "hippodrome": "Vincennes", "pays": "France", "courses": [
                        {"code_course": "R4C1", "prix": "Prix Démo Attelé", "heure": "16:10", "discipline": "Trot attelé", "distance": 2100, "depart": "Autostart", "classe": "Course D"},
                        {"code_course": "R4C2", "prix": "Prix Démo Monté", "heure": "16:45", "discipline": "Trot monté", "distance": 2700, "depart": "Volté", "classe": "Course D"},
                    ]},
                ],
            }
        }

    async def get_program(self, day: date) -> dict[str, Any]:
        return self._program(day)

    async def get_race(self, day: date, code: str, track: str | None = None) -> dict[str, Any]:
        is_trot = code.startswith("R4")
        runners = []
        names = ["ALPHA STAR", "BELLE LIGNE", "COSMOS", "DARK RIVER", "ELITE WIND", "FALCON", "GOLDEN PATH", "HORIZON"]
        for i, name in enumerate(names, 1):
            runners.append({
                "num": i,
                "name": name,
                "idcheval": f"demo-{code}-{i}",
                "age": 4 + (i % 4),
                "sexe": "H" if i % 2 else "F",
                "poids": 52.0 + i if not is_trot else (56 if i % 3 else 60),
                "corde": i if not is_trot else None,
                "distance": 2100 if is_trot else 2400,
                "jockey_driver": f"Driver {i}" if is_trot else f"Jockey {i}",
                "entraineur": f"Entraîneur {i}",
                "ferrure": ["D4", "F4", "DP", "DA"][i % 4] if is_trot else None,
                "musique": ["2a1a4a3a", "5a2aDa1a", "3a3a2a4a", "8a5a2a1a", "1a4a6a2a", "Da2a3a5a", "4a4a5a3a", "7a1a2aDa"][i-1] if is_trot else ["2-1-4-3", "5-2-6-1", "3-3-2-4", "8-5-2-1", "1-4-6-2", "7-2-3-5", "4-4-5-3", "7-1-2-6"][i-1],
                "record": f"1'1{2 + (i%5)}\"{i%10}" if is_trot else None,
                "gains": 20000 + i * 6500,
                "np": False,
            })
        return {"data": {"date": day.isoformat(), "code_course": code, "hippodrome": track or ("Vincennes" if is_trot else "Saint-Cloud"), "partants": runners}}

    async def get_horse_history(self, horse_id: str, discipline: str | None = None) -> dict[str, Any]:
        seed = sum(ord(c) for c in horse_id) % 7
        rows = []
        today = date.today()
        for j in range(10):
            pos = ((seed + j * 2) % 8) + 1
            dq = (seed + j) % 9 == 0
            rows.append({
                "date": (today - timedelta(days=18 * (j + 1))).isoformat(),
                "hippodrome": ["Vincennes", "Enghien", "Saint-Cloud", "Deauville", "Cabourg"][j % 5],
                "discipline": discipline or "Trot attelé",
                "distance": [2100, 2175, 2400, 2700, 2850][j % 5],
                "position": None if dq else pos,
                "disqualifie": dq,
                "reduction_km": 73.0 + (seed * 0.15) + j * 0.08 if "Trot" in (discipline or "Trot") else None,
                "terrain": ["Souple", "Bon", "Très souple"][j % 3],
                "classe": ["Course D", "Course C", "Handicap", "Course E"][j % 4],
                "poids": 54 + ((seed+j) % 6),
                "corde": ((seed+j) % 12) + 1,
                "nb_partants": 12,
            })
        return {"data": {"historique": rows}}

    async def get_results(self, day: date) -> dict[str, Any]:
        return {"data": {"date": day.isoformat(), "results": []}}
