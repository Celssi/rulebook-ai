"""Factory for GM solo game plugins."""

from __future__ import annotations

from src.games.base import GamePlugin


def build_gm_plugin(
    *,
    game_id: str,
    label: str,
    collection: str,
    pdf_sources: dict[str, dict[str, str]],
    mvp_pdfs: list[str],
    all_factions: list[str],
    match_shortcut,
    shortcut_ids: frozenset[str],
    chat_greeting: str,
    ocr_pdfs: list[str] | None = None,
    ingest_all_label: str | None = None,
) -> GamePlugin:
    class GmSoloPlugin(GamePlugin):
        def __init__(self) -> None:
            super().__init__(
                game_id=game_id,
                label=label,
                collection=collection,
                pdf_sources=pdf_sources,
                mvp_pdfs=mvp_pdfs,
                all_factions=all_factions,
                ocr_pdfs=ocr_pdfs or [],
                has_character_sheet=True,
                play_style="gm_solo",
            )

        def chat_greeting(self) -> str:
            return chat_greeting

        def route_before_generic(self, text: str, *, play_entity: dict | None = None) -> dict | None:
            _ = play_entity
            shortcut_id = match_shortcut(text)
            if shortcut_id in shortcut_ids:
                return {"route": "play_multi", "shortcut_id": shortcut_id, "language": "en"}
            return None

        def agent_direct_routes(self) -> frozenset[str]:
            return frozenset({"play_multi"})

        def ingest_all_label(self) -> str:
            if ingest_all_label:
                return ingest_all_label
            return "Full ingest (all PDFs)"

    return GmSoloPlugin()
