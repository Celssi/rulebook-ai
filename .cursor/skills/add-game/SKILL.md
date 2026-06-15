---
name: add-game
description: >-
  Add a new tabletop game to rulebook-ai: plugin, PDF ingest, curated YAML tables,
  character creation, shortcuts, Lonelog, API, and frontend. Use when adding a
  game, porting a zine/PDF, verifying card tables against source PDFs, wiring
  shortcuts, or extending Brambletrek/San Sibilia patterns.
---

# Add a game to rulebook-ai

## Choose scope first

| Scope | When | Template |
|-------|------|----------|
| **PDF-only** | Rules Q&A, no roster/deck play | `src/games/warhammer_40k/plugin.py` |
| **Full play** | Roster, deck, shortcuts, Lonelog | `brambletrek` + `sansibilia` |

Full play always includes a PDF-only plugin layer. You rarely edit `src/rag.py` or `src/agent.py` for PDF-only games.

## Workflow checklist

Copy and track:

```
- [ ] 1. PDFs in docs/<game_id>/ + attribution
- [ ] 2. plugin.py + registry.py
- [ ] 3. python -m src.ingest --game <game_id>
- [ ] 4. Curated YAML (if card/dice tables) + curated.py
- [ ] 5. Verify every table row against PDF (see reference.md)
- [ ] 6. play.py PlayProfile (if roster/Lonelog)
- [ ] 7. Entity model + lonelog.py + actions.py shortcuts
- [ ] 8. api/services/<game>_service.py + api/routes/<game>.py + main.py router
- [ ] 9. prompts.py system prompt branch
- [ ] 10. agent.py node (if shortcut agent route) + plugin.route_before_generic
- [ ] 11. Frontend: PlayPage branches, API client, components
- [ ] 12. scripts/validate_<game>_curated.py + validate_<game>_lonelog.py
- [ ] 13. scripts/validate_shortcuts.py cases (if shortcuts)
- [ ] 14. data/eval/<game>_retrieval_regression.json (optional)
- [ ] 15. docs/HOW_IT_WORKS.md catalog row
- [ ] 16. data/curated/how_to_play/<game_id>.yaml — Finnish guide with PDF start rules + **Sovelluksessa** section (Settings → Character, shortcuts, lonelog)
```

Run validators before declaring done:

```bash
python3 scripts/validate_play_tools.py
python3 scripts/validate_how_to_play.py
python3 scripts/validate_<game>_curated.py
python3 scripts/validate_<game>_lonelog.py   # if PlayProfile
python3 scripts/validate_shortcuts.py        # if shortcuts
python3 scripts/eval_retrieval.py --game <game_id>
```

---

## Step 1 — Plugin + registry

Create `src/games/<game_id>/plugin.py` implementing `GamePlugin` (`src/games/base.py`):

- `game_id`, `label`, `collection`, `pdf_sources`, `mvp_pdfs`, `all_factions`
- `has_character_sheet` / `has_game_state` flags
- Optional hooks: `enhance_query`, `preprocess_question`, `boost_retrieval`, `chat_greeting`, `route_before_generic`, `agent_direct_routes`

Register in `src/games/registry.py`:

```python
from src.games.<game_id>.plugin import PLUGIN as MYGAME_PLUGIN
from src.games.<game_id> import play as _mygame_play  # noqa: F401 — if PlayProfile

_PLUGINS[MYGAME_PLUGIN.game_id] = MYGAME_PLUGIN
```

Import `play` module so `register_play_profile()` runs at startup.

---

## Step 2 — Ingest

```bash
python -m src.ingest --game <game_id>
```

PDF paths are relative to `docs/` keys in `pdf_sources`. Use `ocr_pdfs` in plugin for scan-heavy books.

---

## Step 3 — Curated tables (card/dice lookups)

**Do not index curated tables in Chroma.** They are deterministic lookups in `data/curated/*.yaml` loaded by `src/games/<game_id>/curated.py`.

### YAML rules

- One file per table (or logical group); comment PDF page at top.
- Use quoted rank keys for numbers: `"2":`, `"10":`.
- Face cards: `jack`, `queen`, `king`, `ace` (not `J`/`Q`/`K` in YAML).
- Match PDF column order exactly — wrong column = wrong game behavior.

### curated.py pattern

- `parse_playing_card()` — **must accept virtual-deck format** (`J of hearts`, `Q of diamonds`, `A of spades`). Copy regex from `sansibilia/curated.py` or `brambletrek/curated.py` (`[ajqk]` aliases).
- `_load_yaml()` from `src.settings.CURATED_DIR`
- `@lru_cache` loaders per table
- `lookup_*()` per table dimension
- `format_*_draw()` composing multi-card results
- `all_ranks_valid()` — assert every rank key exists in every required table

### Table verification (mandatory)

For **each** curated table:

1. Open source PDF at cited page; read column headers and row order.
2. Spot-check **every rank** (ace, 2–10, J, Q, K) for at least one suit/color axis.
3. Add assertions to `scripts/validate_<game>_curated.py` with PDF page comments.
4. Test **virtual deck strings** (`J of hearts`), not only `Jack of hearts`.
5. Test combined draws (e.g. day draw: card1 → table A, card2 → table B).

Common mistakes:

| Mistake | Symptom |
|---------|---------|
| Two PDF columns treated as one draw | Character uses max rank instead of trait + role |
| Red/black vs suit confusion | Wrong adjective/location for hearts vs diamonds |
| `J of hearts` not parsed | Empty lookup → `****` in markdown bold |
| Missing rank in YAML | Silent empty string at runtime |
| Indexed table in Chroma instead of YAML | Non-deterministic, expensive lookups |

See [reference.md](reference.md) for San Sibilia / Brambletrek table mapping examples.

---

## Step 4 — Character creation

Two patterns in this repo:

### A — Two cards, two columns (San Sibilia)

- Card 1 rank → **trait** column; card 2 rank → **role** column.
- `format_character_draw(cards)` returns both + archetype string.
- Settings draw: **no lonelog**, **no RAG** — pure curated lookup.
- Persist `character_trait_rank`, `character_role_rank`, `character_cards`, `archetype`.

### B — Single card per table (Brambletrek)

- Reason / Background / Trinket: one card each, band from rank.
- `drawCharacterTable` API for settings; shortcuts may pre-draw + RAG explain.

### Shared rules

- Use `draw_cards()` from `src/play_tools.py` scoped by `game_id` + `char_id`.
- Call `ctx.sync_deck()` before draw, `ctx.refresh_deck()` after.
- Physical deck mode: raise clear error; user reports cards manually.
- Character creation in Settings must **not** call `onSaved` if that closes the modal mid-setup.

---

## Step 5 — Shortcuts

### actions.py contract

```python
SHORTCUTS = [{"id": "...", "label": "...", "kind": "..."}, ...]
SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)

def match_<game>_shortcut(text: str, **ctx) -> str | None: ...
def run_shortcut(shortcut_id: str, **kwargs) -> dict:
    # Returns at minimum user_message; often prompt, kind, static, dice, cards
def shortcuts_for_<entity>(**filters) -> list: ...  # sidebar filter
```

### Shortcut kinds (Brambletrek reference)

| kind | Behavior |
|------|----------|
| `static` | Return text only; no RAG |
| `rag_only` | RAG prompt; no card draw |
| `card_rag` | Draw 1 card + RAG |
| `multi_draw_rag` | Draw N cards + RAG + persist journey state |
| `roll_rag` | Roll dice + RAG |

San Sibilia kinds: `multi_draw`, `roll`, `static`, `rag_only`.

### Service layer (`api/services/<game>_service.py`)

- `run_visit_shortcut(ctx, shortcut_id, ...)` — core logic, persists state, returns `(user_message, answer, sources, route)`.
- `execute_shortcut(ctx, shortcut_id, app=...)` — thin wrapper for API.
- `try_handle_prompt(ctx, prompt, app=...)` — chat path; runs **before** agent (`chat_service.py`).
- Draw shortcuts: update entity, lonelog, chat messages separately (mechanics vs AI prose).

### Agent + plugin routing

- `plugin.route_before_generic()` → `{route: "<game>_multi", shortcut_id}` for matched shortcuts.
- `plugin.agent_direct_routes()` includes that route (skip second LLM synthesize pass).
- Agent node calls **`run_visit_shortcut`**, not raw `run_shortcut`, so state persists.

### Chat vs lonelog (journal games)

| Channel | Content |
|---------|---------|
| **Lonelog** | Compact `d:` draws, short `=>` in AI mode |
| **Chat user** | Mechanics line (cards, table results) |
| **Chat assistant** | Full journal prose (AI narrator) or echo mechanics (player mode) |

Do not log character creation draws to lonelog unless rules say so.

### Frontend UX

- Shortcut click: `flushSync` optimistic user message (`**{label}**`); **do not** set chat `loading` (no "Thinking…" before label shows).
- `handleShortcut` → game-specific API → `setMessages(res.messages)` → `reloadCurrentGame()`.
- Day draw button must use same path as `draw_day` shortcut for chat sync.

Extend `scripts/validate_shortcuts.py` with match phrases and static shortcut smoke tests.

---

## Step 6 — Play roster + Lonelog

`src/games/<game_id>/play.py`:

```python
PlayProfile(
    game_id=...,
    entity_filename="visit.json",  # or character.json
    entity_from_dict=...,
    entity_to_dict=...,
    default_entity=...,
    has_lonelog=True,
    play_settings={...},  # story_mode, card_source, game-specific
    session_extra_keys=[...],  # e.g. pending_journey
)
register_play_profile(PROFILE)
```

Saves layout: `data/saves/<game_id>/<slot_id>/entity.json`, `session.json`, `lonelog.md`.

Game-specific `lonelog.py` wraps `LonelogStore` formatters (`d:`, `=>`, `@`).

---

## Step 7 — API + frontend

| Layer | Path |
|-------|------|
| Routes | `api/routes/<game_id>.py` |
| Service | `api/services/<game_id>_service.py` |
| Register | `api/main.py` `include_router` |
| Client | `frontend/src/api/client.ts` |
| UI | `frontend/src/pages/PlayPage.tsx` branches on `selected_game_id` |
| Components | `frontend/src/components/<game_id>/` |

Return shortcut responses with: `messages`, `entity`, `header`, `sources`, `route` (and `pending_journey` for Brambletrek).

---

## Step 8 — prompts.py

Add `game_id` branch in `build_system_prompt()`:

- Inject entity summary via `format_for_prompt()`
- `story_mode`: player = mechanics only; `ai_narrator` = may synthesize prose
- `card_source`: physical vs virtual deck rules
- Lonelog notation reminder

---

## Step 9 — Agent registration (if needed)

Only when shortcuts use dedicated agent nodes:

1. `src/games/<game_id>/agent.py` — node function
2. `src/agent.py` — import, `add_node`, `add_edge` to synthesize, add to `_DIRECT_ROUTES` and router map

Prefer `try_handle_prompt` + service `execute_shortcut` for API/chat parity.

---

## Pitfalls (learned from production bugs)

1. **`J/Q/K/A` card strings** — virtual deck uses single-letter ranks; parser must handle them.
2. **Empty markdown bold** — `**{empty}**` renders as `****`; fix lookup, not just UI.
3. **Shortcut match ambiguity** — e.g. `"draw two cards"` belongs to character creation, not day draw.
4. **Agent without persist** — raw `run_shortcut` in agent node does not save visit/character.
5. **Duplicate chat sync** — `append_chat_exchange` already calls `sync_messages_to_context`.
6. **Settings character draw** — don't trigger parent `onSaved` that closes modal.
7. **Day draw without chat** — any draw endpoint must append user + assistant messages like shortcuts.

---

## Reference templates

| Game | Best copy-from |
|------|----------------|
| PDF + game state | `warhammer_40k` |
| Journey + adventures + complex shortcuts | `brambletrek` |
| Journal oracle + city tracker + two-card character | `sansibilia` |
| Minimal PDF-only | `warhammer_40k/plugin.py` only |

Detailed file list, lonelog symbols, and PDF verification worksheet: [reference.md](reference.md).
