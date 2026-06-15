"""Game-specific API request models."""

from __future__ import annotations

from pydantic import BaseModel


class VisitCityChangeRequest(BaseModel):
    note: str = ""


class VisitAdvanceRequest(BaseModel):
    days_between: int | None = None


class ApothecariaLocaleRequest(BaseModel):
    locale_id: str


class ApothecariaHuntRequest(BaseModel):
    reagent_name: str


class ApothecariaBuyRequest(BaseModel):
    item_id: str


class ApothecariaShortcutParams(BaseModel):
    locale_id: str | None = None
    reagent_name: str | None = None
    tool_id: str | None = None
    upgrade_id: str | None = None
