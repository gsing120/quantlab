# QuantLab

Multi-lens swing trading system with LLM-augmented research factory.

## What This Is

A quantitative swing trading system for US equities that combines:

- **Statistical ML core:** regime-aware ensemble of momentum, mean-reversion, and quality/value sub-models on daily bars
- **Semantic lens layer:** multiple Claude-powered agents that interpret news, filings, and macro events through specialized perspectives (rates, equity risk, flow, geopolitical, retail narrative, contrarian)
- **Continuous grading:** every lens and strategy is evaluated against forward returns with conditional performance tracking across regimes
- **Deep Research factory:** LLM-orchestrated cycles synthesize academic papers into novel trading theses, derive testable strategies, and feed them into shadow evaluation
- **Runtime LLM selector:** allocates capital across a universe of regime-specialized strategies based on current market state

**Horizon:** 5–20 trading days per position.  
**Data:** Polygon.io (primary), IBKR native (execution-layer).  
**Broker:** Interactive Brokers.

## Project Status

**Sprint 0 — Foundation Setup.** Not yet trading. Not yet backtesting. Building infrastructure.

See `docs/BLUEPRINT.md` for the full 13-layer architecture and sprint plan.

## Setup

### Prerequisites

- Python 3.11+
- `uv` (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git
- IBKR paper trading account
- Polygon.io Developer subscription
- Anthropic API key

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/quantlab.git
cd quantlab

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Copy env template and fill in your keys
cp .env.example .env
# Edit .env with your actual keys — NEVER commit this file

# Run tests to verify setup
uv run pytest

# If all green, you're ready
```

### Environment Variables

See `.env.example` for the complete list. Required:

- `POLYGON_API_KEY` — from https://polygon.io/dashboard
- `ANTHROPIC_API_KEY` — from https://console.anthropic.com
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID` — for paper trading (7497 is the default paper port)

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=quantlab

# Specific test
uv run pytest tests/test_config.py
```

### Code Quality Checks

```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run mypy src/

# All pre-commit hooks
uv run pre-commit run --all-files
```

## Architecture

See `docs/ARCHITECTURE.md` for the layered component overview and `docs/BLUEPRINT.md` for the full specification including sprint plan, risk register, and success criteria.

Key principles:

1. **Deterministic money path, probabilistic intelligence layer.** Trading decisions are made by version-controlled, tested code. LLM outputs become features, never direct signals.
2. **Point-in-time correctness is religion.** Every historical data access uses `as_of_date` semantics.
3. **Continuous grading, gated promotion.** Lens agents, models, and strategies are continuously evaluated; promotions require statistical significance across regime conditions.
4. **Shadow first.** No strategy goes live from backtest alone. Minimum 3 months of paper trading before any real capital.

## Project Structure

```
quantlab/
├── CLAUDE.md              # Project memory for Claude Code sessions
├── README.md              # You are here
├── docs/                  # Architecture, blueprint, decisions log
├── src/quantlab/          # The codebase
├── tests/                 # Tests mirror src structure
├── scripts/               # One-off and CLI scripts
├── notebooks/             # Exploratory analysis
└── data/                  # Local data lake (gitignored)
```

## Discipline

This system will eventually run real money. The build discipline matters:

- Every sprint has a gate. Do not proceed past a gate without passing it.
- Cross-validate backtests against published factor returns (Ken French library) before trusting any result.
- Deflated Sharpe ratio with Effective-N accounting for every performance claim.
- Hard rules: max 3% per position, max 25% per sector, max 150% gross exposure, hard stop on 10% drawdown.

## License

Private project. All rights reserved.

## References

- Marcos López de Prado, *Advances in Financial Machine Learning*
- Ernest Chan, *Quantitative Trading*
- Ken French Data Library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
