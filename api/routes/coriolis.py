"""Coriolis routes."""

from __future__ import annotations

from api.services import coriolis_service as svc
from api.routes.gm_solo_factory import build_gm_router

router = build_gm_router("coriolis", svc, tags=["coriolis"])
