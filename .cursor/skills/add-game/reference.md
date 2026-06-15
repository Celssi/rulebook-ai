# Add-game reference

## Full file map (play-enabled game)

```
docs/<game_id>/*.pdf
data/curated/<game_id>_*.yaml
data/saves/<game_id>/<slot_id>/
data/eval/<game_id>_retrieval_regression.json   # optional

src/games/<game_id>/
  plugin.py          # GamePlugin
  play.py            # PlayProfile registration
  curated.py         # YAML loaders + parse_playing_card + lookups
  actions.py         # SHORTCUTS, match_*, run_shortcut
  agent.py           # optional LangGraph node
  retrieval.py       # optional boost/preprocess
  <entity>.py        # visit.py / character.py — dataclass + to/from dict
  lonelog.py         # game-specific log formatters
  roster.py          # create/list/delete slots
  narrator.py        # optional AI journal synthesis

api/services/<game_id>_service.py
api/routes/<game_id>.py

frontend/src/components/<game_id>/
frontend/src/api/client.ts          # API methods
frontend/src/pages/PlayPage.tsx     # game branches
frontend/src/types.ts               # Header/entity types

scripts/validate_<game_id>_curated.py
scripts/validate_<game_id>_lonelog.py
scripts/validate_shortcuts.py       # add cases for new game
```

---

## PDF table verification worksheet

For each table, fill this before coding YAML:

```markdown
### Table: [name]
- PDF: [file] p.[N]
- Axis 1: [e.g. red vs black suit color / suit name / rank]
- Axis 2: [if any]
- Row order in PDF: [top to bottom — ace first or king first?]
- Column mapping: [which drawn card maps to which column]

| Rank | [axis value 1] | [axis value 2] | Verified |
|------|----------------|----------------|----------|
| ace  |                |                | [ ]      |
| 2    |                |                | [ ]      |
| ...  |                |                | [ ]      |
| king |                |                | [ ]      |

Parser test cards:
- [ ] `Ace of hearts`
- [ ] `J of hearts`  (virtual deck format)
- [ ] Combined draw: [card1] + [card2] → expected text
```

### San Sibilia table map (reference)

| Table | YAML | Card input | Key rule |
|-------|------|------------|----------|
| Character trait | `sansibilia_character_table.yaml` | 1st card rank | Left PDF column |
| Character role | same file | 2nd card rank | Right PDF column |
| Adjective | `sansibilia_adjective_tables.yaml` | 1st card | red = hearts/diamonds |
| Location/event | `sansibilia_location_event_tables.yaml` | 2nd card | red vs black |
| City change | `sansibilia_city_changes.yaml` | pair | same suit OR same rank |
| Day 1 prompts | `sansibilia_journal_prompts.yaml` | — | static list |
| Ending prompts | same | — | static list |
| Ending modes | `sansibilia_ending_modes.yaml` | — | settings only |

Day draw: `format_day_draw(card1, card2)` — card1 = adjective, card2 = location/event.

### Brambletrek table map (reference)

| Table | YAML pattern | Draw count |
|-------|--------------|------------|
| Journey (surface) | per-suit rank rows | 4 cards in shortcut |
| Journey (Aldwund) | depths overlay | 4 cards |
| Reason / Background / Trinket | band by rank | 1 each |
| Recovery | stat + band | 1 |
| Combat setup | multiple lookups | 6 |
| Adventure modules | separate PDF faction | 3 scene cards |
| Legacy | d6 roll | roll_rag shortcut |

---

## parse_playing_card — required regex

Virtual deck (`src/play_tools.py`) emits `"J of hearts"`, not `"Jack of hearts"`.

```python
_CARD_RE = re.compile(
    r"(?i)^(?P<rank>ace|a|king|k|queen|q|jack|j|[2-9]|10)\s+of\s+"
    r"(?P<suit>hearts|diamonds|clubs|spades)$"
)
_RANK_ALIASES = {"a": "ace", "j": "jack", "q": "queen", "k": "king", ...}
```

Return dict: `suit`, `rank_key`, `numeric_value`, `color` (if red/black game).

---

## Shortcut architecture diagram

```
Sidebar button / chat phrase
        │
        ├─► POST /api/<game>/shortcuts/{id}     ─► execute_shortcut()
        │                                         ├─ draw + curated lookup
        │                                         ├─ RAG (if needed)
        │                                         ├─ persist entity + lonelog
        │                                         └─ append_chat_exchange()
        │
        └─► POST /api/chat                       ─► try_handle_prompt() first
                                                  └─ same execute_shortcut path
                                                       │
        Agent mode (if try_handle missed)          │
                └─► route_before_generic()         │
                    └─► <game>_multi_node()      │
                        └─ run_visit_shortcut()  ◄── must match API behavior
```

---

## Brambletrek shortcut IDs

`start_playing`, `journey_day`, `aldwund_day`, `random_character`, `reason`, `background`, `trinket`, `resources`, `combat_setup`, `overcome_odds`, `recovery_health`, `recovery_morale`, `recovery_supplies`, `random_legacy`, `legacy_overview`, `reason_ending`, `adventure_overview`, `adventure_scene`

`adventure_scene` hidden in sidebar when `active_adventure` is empty.

## San Sibilia shortcut IDs

`draw_character`, `draw_day`, `day_one_prompts`, `ending_prompts`, `roll_days_between`, `city_change_help`

When `visit_complete`: sidebar shows only `ending_prompts`, `city_change_help`.

---

## Lonelog symbols (PlayProfile games)

| Symbol | Meaning |
|--------|---------|
| `@` | Player action |
| `d:` | Draw |
| `->` | Result |
| `=>` | Consequence / narrative summary |
| `?` | Oracle question |

Game `lonelog.py` should keep lines compact; full prose goes to chat in AI narrator mode.

---

## validate_*_curated.py template

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.<game_id>.curated import (
    all_ranks_valid,
    parse_playing_card,
    format_<main_draw>,
    lookup_<table>,
)

def main() -> int:
    assert all_ranks_valid()
    # PDF p.N spot checks — one assertion per table axis
    assert parse_playing_card("J of hearts")["rank_key"] == "jack"
    # Combined draw from PDF example on p.N
    sample = format_<main_draw>("4 of spades", "Queen of diamonds")
    assert sample["field"] == "expected from PDF"
    print("validate_<game>_curated: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Story mode + chat split (journal games)

| story_mode | Chat assistant after draw |
|------------|---------------------------|
| `player` | Mechanics only (or same as user message) |
| `ai_narrator` | `synthesize_journal_entry()` — long prose |

Lonelog in AI mode: `synthesize_lonelog_summary()` → short `=>` line.

Implement in service layer (`perform_day_draw`, not in frontend).

---

## Frontend PlayPage integration points

1. `load<Game>()` — header, roster, shortcuts, lonelog, deck
2. `handleShortcut(id)` — optimistic `flushSync` user bubble; game API; no `loading` state
3. `handleDayDraw()` — same optimistic pattern for San Sibilia
4. `reloadCurrentGame()` — refresh lonelog/messages after mutations
5. `SettingsDialog` — play_settings (`story_mode`, `card_source`, game-specific)
6. `PlayPanel` — pass `shortcuts`, `onShortcut`, game-specific day panel

---

## Ingest + eval

```bash
python -m src.ingest --game <game_id>
python3 scripts/eval_retrieval.py --game <game_id>
```

Add 5–10 regression questions in `data/eval/` with expected source files/pages.

---

## Attribution

Add game credit to README and any in-app about/attribution if required by license.
