# How rulebook-ai works

Local tabletop rules assistant. You supply PDFs in `docs/`; the app indexes them locally and answers questions with retrieval-augmented generation (RAG) via Ollama.

## Purpose

- **Personal study / at-table helper** — not an official rules arbiter.
- **Fully local** — PDFs, vector index, and LLM calls stay on your machine.
- **Multi-game** — each game has its own Chroma collection and optional game-specific tools (character sheet, shortcuts, curated tables).

## Data flow

```mermaid
flowchart LR
  PDFs[docs/game_id/*.pdf]
  Ingest[src/ingest.py]
  Chroma[data/chroma/collection]
  Retrieve[src/rag.py + game plugin]
  LLM[Ollama chat model]
  UI[React UI + FastAPI]

  PDFs --> Ingest
  Ingest --> Chroma
  UI --> Retrieve
  Retrieve --> Chroma
  Retrieve --> LLM
  LLM --> UI
```

1. **Ingest** — PDF text (or OCR for image pages) is cleaned, chunked, embedded with `nomic-embed-text`, and stored in Chroma with metadata (`source_file`, `page`, `faction`, etc.).
2. **Query** — User question is optionally enhanced by the active game plugin, then hybrid retrieval (dense + lexical + RRF) pulls candidate chunks. Optional **cross-encoder rerank** reorders candidates (all games). Game plugins may **boost** results last (prepend pinned chunks).
3. **Answer** — Top chunks plus a system prompt are sent to the chat model; citations come from chunk metadata.

## Modes

| Mode | Behaviour |
|------|-----------|
| **RAG** | Direct retrieval + single LLM call. Faction filters in Settings apply. |
| **Agent** | LangGraph router sends dice/card/Leviathan/shortcut requests to tools first, then RAG when needed. |
| **Slash commands** | `/roll`, `/draw`, `/deck reset` bypass retrieval for instant replies. |

Shared table tools (dice, 52-card deck) live in [`src/play_tools.py`](../src/play_tools.py) and are keyed by `game_id` so each game mode keeps its own deck.

## Game registry

Games are registered in [`src/games/registry.py`](../src/games/registry.py). Each game implements a **GamePlugin** ([`src/games/base.py`](../src/games/base.py)) with:

- **Metadata** — `game_id`, `label`, Chroma `collection`, PDF sources, factions, feature flags (`has_game_state`, `has_character_sheet`)
- **Optional hooks** — query enhancement, faction inference, retrieval boosting, agent routing, chat greeting, UI sidebar rendering

[`src/config.py`](../src/config.py) holds global paths and Ollama settings; per-game PDF lists live in each plugin module.

Current games:

| ID | Label | Extra features |
|----|-------|----------------|
| `40k` | Warhammer 40,000 | Battle game state, Leviathan unit list, codex/datasheet retrieval |
| `brambletrek` | Brambletrek | Gnawborn roster, Lonelog, story/card modes, curated YAML, journey/adventure shortcuts |

## Key files

| Path | Role |
|------|------|
| [`api/main.py`](../api/main.py) | FastAPI app (REST + SSE chat) |
| [`frontend/`](../frontend/) | React dashboard (play mode layout) |
| [`src/config.py`](../src/config.py) | Paths, models, chunk sizes |
| [`src/games/registry.py`](../src/games/registry.py) | Game plugin lookup |
| [`src/ingest.py`](../src/ingest.py) | PDF → Chroma indexing CLI |
| [`src/rag.py`](../src/rag.py) | Generic hybrid retrieval and answer generation |
| [`src/agent.py`](../src/agent.py) | LangGraph tool router |
| [`src/play_tools.py`](../src/play_tools.py) | Dice and deck primitives |
| [`src/tools.py`](../src/tools.py) | Agent-facing tools (RAG search, Leviathan list) |
| [`src/prompts.py`](../src/prompts.py) | Per-game system prompts |
| [`src/games/saves/`](../src/games/saves/) | Generic play roster, session, Lonelog |
| [`data/curated/`](../data/curated/) | YAML reference data (not indexed; used for lookups) |
| [`data/chroma/`](../data/chroma/) | Vector index (gitignored) |
| [`data/eval/`](../data/eval/) | Retrieval regression cases |

## Retrieval profiles

Configured in **Settings** (shared by all games):

- **Fast** — dense-only, smaller candidate pool
- **Balanced** — hybrid retrieval (dense + lexical + RRF), medium pool
- **Quality** — hybrid with larger pool (best recall)
- **Quality+ rerank** — hybrid + local cross-encoder rerank (`cross-encoder/ms-marco-MiniLM-L-6-v2` by default; override with `RERANK_MODEL`)

Pipeline in [`src/rag.py`](../src/rag.py): hybrid → optional rerank ([`src/retrieval_core.py`](../src/retrieval_core.py)) → `GamePlugin.boost_retrieval` → top-k to LLM.

Game plugins may raise `top_k` or inject page-specific nodes (e.g. Brambletrek rulebook tables) **after** rerank.

## Brambletrek session data

Per-game save slots live under `data/saves/{game_id}/{slot_id}/`. Games with a registered **PlayProfile** (`src/games/saves/`) get:

| File | Contents |
|------|----------|
| `entity.json` or game-specific name (e.g. `character.json`) | Slot entity (character sheet, campaign, etc.) |
| `session.json` | Deck, chat, play settings, game-specific `extra` fields |
| `lonelog.md` | [Lonelog](https://lonelog.readthedocs.io/) v1.5 session log — core symbols (`@`, `?`, `d:`, `->`, `=>`), tags, sessions/scenes, add-on blocks |

Register a new game by defining a `PlayProfile` and calling `register_play_profile()` (see `src/games/brambletrek/play.py`).

## Adding a new game

1. Create `src/games/<game_id>/plugin.py` implementing `GamePlugin` (copy an existing plugin as template).
2. Register it in [`src/games/registry.py`](../src/games/registry.py).
3. Add PDFs under `docs/<game_id>/`.
4. Run `python -m src.ingest --game <game_id>`.
5. *(Optional)* Add curated YAML in `data/curated/` and a `scripts/validate_<game>_curated.py` smoke script.
6. *(Optional)* Add `data/eval/<game>_retrieval_regression.json` and run `scripts/eval_retrieval.py`.
7. *(Optional)* For multi-slot play (roster, deck/chat per slot, Lonelog), add `src/games/<game_id>/play.py` with a `PlayProfile` and import it from `registry.py` (see Brambletrek).

You should **not** need to edit `src/rag.py` or `src/agent.py` for a PDF-only game — only the plugin and UI.

## What stays shared

- Ollama chat + embedding models
- Chroma storage layout (`data/chroma/<collection>`)
- Ingest pipeline (chunking, OCR cache)
- Dice/deck tools and slash commands
- Retrieval profiles and eval harness

## Validation (no Ollama required)

```bash
python3 scripts/validate_play_tools.py
python3 scripts/validate_brambletrek_curated.py   # Brambletrek only
python3 scripts/validate_brambletrek_lonelog.py   # roster + Lonelog
python3 scripts/eval_retrieval.py --game 40k
python3 scripts/eval_retrieval.py --game brambletrek
```
