# QuantLab — Claude Code Project Memory

## Project Overview

Multi-lens swing trading system. Daily-bar US equity swing trades (5–20 day holds) via IBKR, data from Polygon.io, strategy selection by regime-aware LLM. Full blueprint in `docs/BLUEPRINT.md`.

**Current phase:** Sprint 0 (foundation setup). Not yet trading. Not yet backtesting. Building infrastructure.

## Critical Rules (Non-Negotiable)

1. **Point-in-time correctness is religion.** Every piece of historical data has two timestamps: what it refers to, and when we learned it. No exceptions. Any function that accesses data must accept an `as_of_date` parameter and must not use data newer than that date.

2. **No LLM call produces a trading signal directly.** LLM outputs become features stored in the feature store. Statistical models (LightGBM etc.) consume those features and produce trading signals. The two paths stay architecturally separate.

3. **All features are pure functions of `(panel, as_of_date)`.** No side effects, no hidden state, no shortcuts. Unit tests must verify no forward-information leak.

4. **Every external API call has retry logic, rate limiting, and structured error handling.** Polygon, Anthropic, IBKR — all three. No naked requests.

5. **Every LLM call is logged with model version, prompt version, input, output, timestamp.** Structured logging via `structlog` to both local files and queryable storage.

6. **Tests before features.** If you're about to add a new component, write a failing test first. Exceptions must be justified in a comment.

7. **Never commit secrets.** API keys go in environment variables loaded via `.env` (which is gitignored). Use `python-dotenv`. If you see me paste a key, refuse to write it to a file.

## Tech Stack (Committed)

- Python 3.11+
- Dependency management: `uv` (preferred)
- Pre-commit hooks: `ruff` (lint), `mypy` (types), `pytest` (tests)
- Data storage: Apache Parquet via `polars`
- Structured queries: `duckdb` over Parquet files
- Vector DB: `pgvector` over local Postgres, or `lancedb` if prefer file-based (decide later)
- ML: `lightgbm` primary, `tabpfn` for ensemble later
- Validation: custom Combinatorial Purged CV implementation (reference: `mlfinlab` and `skfolio`)
- LLM: Cowork-only (see ADR-005). No `anthropic` SDK usage in Python. Lens calls and all other LLM-mediated work are scheduled Cowork tasks; Python reads the JSON they emit to `data/research/lens_outputs/` and `data/cowork_outputs/`.
- Broker: `ib_insync`
- Exchange calendar: `pandas_market_calendars`
- Logging: `structlog`
- Config: `pydantic-settings` with `.env` loading
- CLI: `typer` for any CLI tooling
- Task orchestration: plain Python + `APScheduler` for dev; consider `prefect` if complexity grows

## Directory Structure

```
quantlab/
├── CLAUDE.md              # This file
├── README.md              # Project overview
├── pyproject.toml         # uv config
├── .env.example           # Template for secrets (no real keys)
├── .gitignore
├── .pre-commit-config.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md       # ADRs
│   ├── BLUEPRINT.md       # Full 13-layer blueprint
│   └── QUESTIONS.md       # Open questions for human review
├── src/quantlab/
│   ├── __init__.py
│   ├── config.py          # Pydantic settings
│   ├── logging.py         # structlog setup
│   ├── data/              # Layer 1: data infrastructure
│   ├── features/          # Layer 2: numerical features
│   ├── labels/            # Layer 4
│   ├── validation/        # Layer 7
│   ├── models/            # Layer 6
│   ├── regime/            # Layer 5
│   ├── lenses/            # Layer 3 (later sprint)
│   ├── portfolio/         # Layer 8 (later)
│   ├── execution/         # Layer 9 (later)
│   └── research/          # Layers 12, 13 (later)
├── tests/                 # Mirrors src structure
├── scripts/               # One-off and CLI scripts
├── notebooks/             # Exploratory analysis (gitignored output)
└── data/                  # Local data lake (gitignored)
    ├── prices/
    ├── corporate_actions/
    ├── adjustments/
    └── universe/
```

### Deferred Directories (Sprint 6+)

The research loop (Layer 12/13) will add `data/research/` with subdirectories
for papers, paper cards, corpus index, theses, strategies, backtests, and
graveyard. These are NOT created in Sprint 0. See ADR-004 in docs/DECISIONS.md.

## Sprint 0 Tasks (Current)

In order:

1. Initialize `pyproject.toml` with `uv` and the committed dependencies
2. Set up pre-commit hooks
3. Create `.env.example` with placeholder keys for: `POLYGON_API_KEY`, `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID`, `IBKR_ACCOUNT_ID`, `IBKR_MODE`. No `ANTHROPIC_API_KEY` — see ADR-005.
4. Implement `src/quantlab/config.py` with Pydantic settings loading from env
5. Implement `src/quantlab/logging.py` with structured JSON logging
6. Write a trivial test and CI config (GitHub Actions running pytest on PR)
7. Stub out the directory structure with `__init__.py` files and docstrings
8. Write `README.md` with setup instructions

**Sprint 0 gate:** Fresh clone → `uv sync` → `pytest` all green → pre-commit hooks catch a deliberate violation → `.env.example` complete → all docs in place.

## Sprint 1 Tasks (Next — DO NOT start before Sprint 0 gate passes)

Will be added as a new section here when Sprint 0 is complete. Preview:
- Polygon API client with rate limiting
- Parquet storage layer for prices
- Corporate actions ingestion
- `as_of_date` adjustment computation
- Exchange calendar integration
- 10-year historical backfill for S&P 500 universe
- Cross-validation against Yahoo Finance
- Triple-barrier labeling
- CPCV implementation
- Baseline LightGBM momentum model
- **Ken French momentum factor correlation check (>0.9 required)**

## How I Want You To Work

**When starting a session:** Read this file. Check `docs/DECISIONS.md` for recent architecture decisions. Confirm what we're working on.

**When writing code:** Match the existing style. Run `ruff check` and `mypy` mentally before suggesting code. Add type hints everywhere. Write docstrings in Google style.

**When implementing a new component:**
1. Write the test first
2. Write the minimum code to pass the test
3. Add docstring and type hints
4. Run the full test suite
5. Commit with descriptive message

**When you encounter an ambiguity:** Ask me. Do not guess. If I'm absent, write the question in `docs/QUESTIONS.md` and use the most conservative reasonable choice.

**When you detect a likely bug in something I asked for:** Tell me. Don't silently "fix" it to what you think I meant. Surface the ambiguity.

**Commit discipline:** Small focused commits. Atomic. Descriptive messages in conventional-commits style (feat:, fix:, test:, docs:, refactor:, chore:).

**Branch discipline:** Main is protected. Work in feature branches. PR to main. Even solo, the discipline matters because future-me reviews past-me's code.

## What Not To Do

- Don't install dependencies I haven't approved. If a new one is needed, tell me why and wait for confirmation.
- Don't bypass pre-commit hooks. If a hook fails, fix the code, don't disable the hook.
- Don't write "fix typo" commits on master. Use branches.
- Don't hardcode paths. Use `pathlib` and config.
- Don't use `print` for anything other than throwaway scripts. Use the structured logger.
- Don't catch and swallow exceptions. Log and re-raise, or handle specifically with intent.
- Don't add complexity for flexibility I haven't asked for. YAGNI applies.
- Don't reach for async/await unless it's genuinely needed. Sync code is easier to reason about.

## Known Gotchas

(Populate as we encounter them. Starting list:)

- Polygon's free tier has tight rate limits. Use the Developer tier or better. Rate-limit client-side.
- IBKR paper and live accounts use different ports (7497 paper, 7496 live). Config must distinguish.
- TWS vs IB Gateway: Gateway is preferred for long-running connections.
- Pandas market calendars can be surprising for half-days and obscure holidays. Cross-check.
- Polygon's corporate actions feed requires separate handling from the prices endpoint.
- Corporate action errors in historical data are the #1 silent backtest killer. Cross-validate splits/dividends against Yahoo Finance on sample.

## References

- Full blueprint: `docs/BLUEPRINT.md`
- Decision log: `docs/DECISIONS.md`
- Ken French data library (validation benchmark): https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- López de Prado *Advances in Financial Machine Learning*
- Ernest Chan *Quantitative Trading*
