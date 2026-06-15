"""Cosmere API routes."""

from __future__ import annotations

from api.services import cosmere_service as service_module
from api.routes.gm_solo_factory import build_gm_router

router = build_gm_router("cosmere", service_module, tags=["cosmere"])
