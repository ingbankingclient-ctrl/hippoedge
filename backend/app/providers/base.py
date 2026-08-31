from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class ProviderError(RuntimeError):
    pass


class RacingProvider(ABC):
    name: str

    @abstractmethod
    async def get_program(self, day: date) -> dict[str, Any]: ...

    @abstractmethod
    async def get_race(self, day: date, code: str, track: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    async def get_horse_history(self, horse_id: str, discipline: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    async def get_results(self, day: date) -> dict[str, Any]: ...
