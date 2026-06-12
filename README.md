# rulebook-ai

Local rules assistant with selectable game modes:
- **Warhammer 40k** (Leviathan Space Marines and Tyranids)
- **Brambletrek**

- **LLM:** Ollama ([Gemma 4](https://ollama.com/library/gemma4))
- **RAG:** LlamaIndex + ChromaDB
- **UI:** React dashboard + FastAPI
- **OCR:** Tesseract fallback for image-only PDFs

Use your own PDFs in `docs/`.

## Requirements

1. [Ollama](https://ollama.com/download) (recent release for [Gemma 4](https://ollama.com/library/gemma4))
2. Python 3.11+
3. Tesseract:

```bash
brew install tesseract
```

## Step-by-step setup

### 1) Go to project directory

```bash
cd ~/Koodit/rulebook-ai
```

### 2) Confirm PDFs exist in `docs/`

For 40k (minimum):

- `Warhammer-40k-Core-Rules.pdf`
- `Adeptus Astartes Cards.pdf`
- `Tyranid Cards.pdf`

For Brambletrek (place PDFs under `docs/brambletrek/`):

| File | Indexed? | Notes |
|------|----------|--------|
| `Brambletrek_-_Complete_Digital_Edition.pdf` | **Yes** (default) | Core rules, Legacies, journey/combat, **Secrets of the World Tree**, **Dungeons of Dragonkeep**, **Pumpkin Party**, **First Frost** |
| `Brambletrek_-_A_Birthday_of_Wonders.pdf` | Full ingest only | Not in Complete Digital Edition |
| `Brambletrek_-_Winter_Gift.pdf` | Full ingest only | Not in Complete Digital Edition |

Do not keep separate Core Rulebook, Pumpkin Party, or First Frost PDFs — they duplicate content inside Complete Digital Edition.

After changing sources, re-ingest: `python -m src.ingest --game brambletrek --all`

### 3) Create virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### 4) Pull Ollama models

Default model (M4 Mac with 32GB+ RAM, e.g. 48GB):

```bash
ollama pull gemma4:31b
ollama pull nomic-embed-text
```

Lighter alternatives:

```bash
ollama pull gemma4:26b   # MoE, ~18 GB — good balance
ollama pull gemma4:e4b   # ~10 GB — laptops with 16GB RAM
```

### 5) Check Ollama integration

```bash
python scripts/check_ollama.py
```

### 6) Build game indexes

40k quick index:

```bash
python -m src.ingest --game 40k
```

40k full index (all PDFs):

```bash
python -m src.ingest --game 40k --all
```

Brambletrek (Complete Digital Edition + optional separate adventures):

```bash
python -m src.ingest --game brambletrek --all
```

MVP ingest indexes only Complete Digital Edition; `--all` adds Birthday of Wonders and Winter Gift.

### 7) Run the app

**Quick start (recommended):** one script creates the venv, installs deps, checks Ollama, builds missing indexes, and starts the React UI + API:

```bash
chmod +x run.sh   # once
./run.sh
```

Open **http://127.0.0.1:5173** (React dashboard). The API runs on **http://127.0.0.1:8000**.

First run may take a while (Ollama model pulls, PDF indexing, and `npm install` in `frontend/`). To skip slow steps:

```bash
./run.sh --skip-ingest --skip-checks          # dev: skip indexing
./run.sh --skip-ollama --skip-ingest          # offline UI, no model checks
```

Bootstrap flags: `--skip-ollama`, `--skip-ingest`, `--skip-checks`, `--ingest-all` (full PDF set when indexing).

**Manual start** (two terminals):

```bash
# Terminal 1 — API
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000

# Terminal 2 — React UI
cd frontend && npm install && npm run dev
```

**Production build** (single server serves API + static frontend):

```bash
cd frontend && npm run build
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Switching chat model

Embeddings stay the same (`nomic-embed-text`), so you can switch chat model without re-indexing.

```bash
export OLLAMA_CHAT_MODEL=gemma4:26b
uvicorn api.main:app --reload --port 8000
```

Apple Silicon MLX build (lower RAM):

```bash
export OLLAMA_CHAT_MODEL=gemma4:26b-mlx
```

## Using Claude (optional)

You can use Anthropic Claude for chat answers while keeping local Ollama embeddings (`nomic-embed-text`). No re-indexing is needed when switching providers.

1. Set your API key in one of these places (do not commit it):

**Project `.env`** (gitignored):

```bash
ANTHROPIC_API_KEY=your-key-here
```

**Shell export** (session only):

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

2. In **Settings → RAG**, choose **Chat provider → Claude (cloud)**.

Default Claude model is `claude-sonnet-4-20250514`. Override with:

```bash
export CLAUDE_CHAT_MODEL=claude-opus-4-20250514
```

Ollama must still be running for embeddings and indexing.

## OCR behavior

`Codex - Tyranids (10th Edition).pdf` is image-only; OCR runs automatically.

First run can take 10–30 minutes; OCR output is cached in `data/ocr_cache/`.

```bash
# Build OCR cache only (no embedding)
python -m src.ingest --ocr-only

# Force OCR refresh (ignore cache)
python -m src.ingest --all --ocr
```

## Dice and card tools

Works in **RAG** and **Agent** mode. Slash commands skip retrieval and return immediately.

The assistant can roll dice and draw from a standard 52-card deck (per game mode in the UI session).

| Command | Example | Behavior |
|---------|---------|----------|
| Roll | `/roll 2d6+1` | Roll dice (`d20`, `3d8-2`, etc.) |
| Draw | `/draw` or `/draw 3` | Draw from the current game's deck |
| Reset deck | `/deck reset` | New shuffled 52-card deck for this game mode |

**Natural language (Agent mode, or RAG for simple rolls/draws):**

- `roll 2d6+1` or `Roll 2d6 for my charge`
- `draw a card`
- `draw for my reason for adventure and explain it` (draw + rules lookup)
- `Shuffle the deck` / `reset deck`

**Settings panel:** deck remaining count, Draw 1, Reset deck, and a quick roll field.

**Brambletrek shortcuts (Play panel, Brambletrek mode only):** random character, **Journey / Aldwund day** (curated core tables pp. 24–27 + **Today's draws**), **Adventure scene (3 cards)** when an adventure is selected (PDF via RAG only), combat setup, recovery, Legacy, **Reason ending (p. 36)**, and **Active adventure overview**.

Deck state persists per character (Brambletrek) or per game (40k) until you reset or switch. Invalid dice notation returns a short error (e.g. use `2d6`, not `2x6`).

Validate dice/deck logic without Ollama:

```bash
python3 scripts/validate_play_tools.py
python3 scripts/validate_brambletrek_lonelog.py
python3 scripts/validate_tools.py
```


- **Game selector (header):** `Warhammer 40,000` or `Brambletrek`
- **RAG mode:** direct retrieval from indexed docs
- **Agent mode:** tool-routed answers (dice, cards, Leviathan lists, rules) (rules, Leviathan lists on 40k, dice, cards)
- **40k mode only:** Game State panel (army, opponent, round, phase)
- **Brambletrek mode:** multi-Gnawborn roster; each character has its own sheet, deck, chat, and **[Lonelog](https://lonelog.readthedocs.io/)** session file under `data/saves/brambletrek/{id}/`
- **Story mode:** **Player-led** (you write `@` actions; AI explains rules) or **AI narrator** (AI adds `=>` narrative after events)
- **Card source:** **Physical deck** (report pulls — synced to virtual deck) or **Virtual** (app/AI draws)
- **Lonelog:** append-only `lonelog.md` per character; `/log …` slash command; sidebar viewer + download
- **Curated YAML** (`data/curated/brambletrek_*.yaml`): core **journey**, Aldwund depths, recovery, items, legacies, **reason endings** — plus **Today's draws** for Hyhill journey only. Adventure modules use **metadata only** in YAML; scenes come from the indexed PDF via RAG.
- **Adventures:** set **Active adventure** on the sheet, then use **Adventure scene** or ask for today's scenes (Pumpkin Party, First Frost, World Tree, and Dragonkeep are in Complete Digital Edition; Birthday and Winter Gift need full ingest). Say **Hyhill journey** or use **Journey day** for core tables while an adventure is active.
- **Table deck (Play panel):** one shuffled 52-card deck per Gnawborn; draw, report physical cards, or reset from the Play panel or chat
- **Retrieval profile (Settings):**
  - `Fast`: dense-only, smaller candidate pool
  - `Balanced`: hybrid retrieval (dense + lexical), medium candidate pool
  - `Quality`: hybrid retrieval with larger candidate pool (best recall)
  - `Quality+ rerank`: hybrid + local cross-encoder rerank (all games; requires `sentence-transformers`)

## Common issues

### npm not found

Install [Node.js 18+](https://nodejs.org/) and run `./run.sh` again.

### Gemma 4 pull fails

```bash
ollama --version
```

Upgrade Ollama if needed. Then retry `ollama pull gemma4:31b`.

### OCR fails

```bash
tesseract --version
```

## Project layout

See **[docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md)** for architecture, data flow, and how to add a new game.

| Path | Purpose |
|------|---------|
| `docs/` | Rulebooks and cards |
| `docs/HOW_IT_WORKS.md` | Architecture and extension guide |
| `data/chroma/` | Vector index |
| `data/ocr_cache/` | OCR cache |
| `src/games/` | Per-game plugins (config, retrieval, UI hooks) |
| `src/ingest.py` | PDF -> chunks -> Chroma |
| `src/rag.py` | Retrieval + response |
| `src/agent.py` | LangGraph agent |
| `src/tools.py` | Dice, cards, Leviathan list, RAG search |
| `api/` | FastAPI REST + SSE chat |
| `frontend/` | React dashboard |
| `scripts/validate_tools.py` | Dice/deck checks (no Ollama) |

## Notes

OCR text may contain recognition errors. For exact values, prefer card tables and original docs.
