from __future__ import annotations

from datetime import date
from typing import Any
import httpx

from .base import ProviderError, RacingProvider
from ..utils import sanitize_objective_payload


class TurfBzhProvider(RacingProvider):
    name = "turfbzh"

    def __init__(self, base_url: str, api_key: str | None):
        if not api_key:
            raise ProviderError("HIPPOEDGE_TURFBZH_API_KEY est requis pour le fournisseur turfbzh")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "X-API-Key": self.api_key}
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.get(f"{self.base_url}/{path.lstrip('/')}", params=params or {}, headers=headers)
        if r.status_code >= 400:
            raise ProviderError(f"TurfBZH {r.status_code}: {r.text[:300]}")
        payload = r.json()
        if isinstance(payload, dict) and payload.get("error"):
            raise ProviderError(str(payload["error"]))
        # Firewall: odds, provider AI scores, popularity, tips and editorial rankings are removed here.
        return sanitize_objective_payload(payload)

    async def get_program(self, day: date) -> dict[str, Any]:
        return await self._get("programme", {"date": day.isoformat()})

    async def get_race(self, day: date, code: str, track: str | None = None) -> dict[str, Any]:
        params = {"hippodrome": track} if track else None
        return await self._get(f"courses/{day.isoformat()}/{code}", params)

    async def get_horse_history(self, horse_id: str, discipline: str | None = None) -> dict[str, Any]:
        params = {"discipline": discipline} if discipline else None
        return await self._get(f"chevaux/{horse_id}/historique", params)

    async def get_results(self, day: date) -> dict[str, Any]:
        return await self._get("resultats", {"date": day.isoformat()})
