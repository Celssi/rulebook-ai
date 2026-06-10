# rulebook-ai

Local rules assistant with selectable game modes:
- **Warhammer 40k** (Leviathan Space Marines and Tyranids)
- **Brambletrek**

- **LLM:** Ollama ([Gemma 4](https://ollama.com/library/gemma4))
- **RAG:** LlamaIndex + ChromaDB
- **UI:** Streamlit
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

```bash
streamlit run app/streamlit_app.py
```

## Switching chat model

Embeddings stay the same (`nomic-embed-text`), so you can switch chat model without re-indexing.

```bash
export OLLAMA_CHAT_MODEL=gemma4:26b
streamlit run app/streamlit_app.py
```

Apple Silicon MLX build (lower RAM):

```bash
export OLLAMA_CHAT_MODEL=gemma4:26b-mlx
```

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

The assistant can roll dice and draw from a standard 52-card deck (per game mode in the UI session).

**Natural language (Agent mode, or RAG for simple rolls/draws):**

- `roll 2d6+1`
- `draw a card`
- `draw for my reason for adventure and explain it` (draw + rules lookup)

**Explicit commands (bypass retrieval, instant reply):**

- `/roll 2d6+1` or `/roll d20`
- `/draw` or `/draw 3`
- `/deck reset`

**Sidebar:** deck remaining count, Draw 1, Reset deck, and a quick roll field.

**Brambletrek shortcuts (sidebar, Brambletrek mode only):** random character, **Journey / Aldwund day** (curated core tables pp. 24–27 + **Today's draws**), **Adventure scene (3 cards)** when an adventure is selected (PDF via RAG only — no curated journey rows), combat setup, recovery, Legacy, **Reason ending (p. 36)**, and **Active adventure overview**. Multi-card shortcuts draw from the deck first, then RAG.

Deck state persists for the selected game until you reset or switch game mode. Invalid dice notation returns a short error (e.g. use `2d6`, not `2x6`).

Validate dice/deck logic without Ollama:

```bash
python3 scripts/validate_play_tools.py
```

## UI modes

- **Game selector (sidebar):** `Warhammer 40,000` or `Brambletrek`
- **RAG mode:** direct retrieval from indexed docs
- **Agent mode:** tool-routed answers (dice, cards, Leviathan lists, rules) (rules, Leviathan lists on 40k, dice, cards)
- **40k mode only:** Game State sidebar (army, opponent, round, phase)
- **Brambletrek mode:** rules/dice helper; **Your Gnawborn** sheet (Reason, Legacy, **Active adventure**, stats) persists in `data/saves/brambletrek_character.json`
- **Curated YAML** (`data/curated/brambletrek_*.yaml`): core **journey**, Aldwund depths, recovery, items, legacies, **reason endings** — plus sidebar **Today's draws** for Hyhill journey only. Adventure modules use **metadata only** in YAML; scenes come from the indexed PDF via RAG.
- **Adventures:** set **Active adventure** on the sheet, then use **Adventure scene** or ask for today's scenes (Pumpkin Party, First Frost, World Tree, and Dragonkeep are in Complete Digital Edition; Birthday and Winter Gift need full ingest). Say **Hyhill journey** or use **Journey day** for core tables while an adventure is active.
- **Table deck (sidebar):** one shuffled 52-card deck per selected game mode; draw and reset from the sidebar or chat
- **Retrieval profile (sidebar):**
  - `Fast`: dense-only, smaller candidate pool
  - `Balanced`: hybrid retrieval (dense + lexical), medium candidate pool
  - `Quality`: hybrid retrieval with larger candidate pool (best recall)

## Dice and cards

Works in **RAG** and **Agent** mode. Slash commands skip retrieval and return immediately.

| Command | Example | Behavior |
|---------|---------|----------|
| Roll | `/roll 2d6+1` | Roll dice (`d20`, `3d8-2`, etc.) |
| Draw | `/draw` or `/draw 3` | Draw from the current game’s deck |
| Reset deck | `/deck reset` | New shuffled 52-card deck for this game mode |

**Natural language (Agent mode):**

- `Roll 2d6 for my charge`
- `Draw a card`
- `Shuffle the deck` / `reset deck`
- Brambletrek: `Draw for reason for adventure` combines a draw with rules lookup when indexed

Deck state is stored in the Streamlit session **per game mode** (40k and Brambletrek each keep their own deck). Switching game in the sidebar does not mix decks.

**Validate tools (no Ollama):**

```bash
python3 scripts/validate_tools.py
```

**Invalid notation:** use forms like `2d6` or `2d6+1`. Errors explain the expected format.

## Retrieval regression eval

Run retrieval-only checks (no answer judging):

```bash
# 40k cases
python3 scripts/eval_retrieval.py --game 40k

# Brambletrek cases
python3 scripts/eval_retrieval.py --game brambletrek
```

Useful comparisons:

```bash
# Dense-only baseline (40k)
python3 scripts/eval_retrieval.py --game 40k --no-hybrid

# Quality-style wider candidate pool (Brambletrek)
python3 scripts/eval_retrieval.py --game brambletrek --candidate-k 70 --top-k 8
```

## Common issues

### `streamlit: command not found`

```bash
python -m streamlit run app/streamlit_app.py
```

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

| Path | Purpose |
|------|---------|
| `docs/` | Rulebooks and cards |
| `data/chroma/` | Vector index |
| `data/ocr_cache/` | OCR cache |
| `src/ingest.py` | PDF -> chunks -> Chroma |
| `src/rag.py` | Retrieval + response |
| `src/agent.py` | LangGraph agent |
| `src/tools.py` | Dice, cards, Leviathan list, RAG search |
| `app/streamlit_app.py` | Streamlit UI |
| `scripts/validate_tools.py` | Dice/deck checks (no Ollama) |

## Notes

OCR text may contain recognition errors. For exact values, prefer card tables and original docs.
