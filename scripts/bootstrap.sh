#!/usr/bin/env bash
# QuantLab bootstrap script — one-command setup for a fresh clone.
#
# Usage: ./scripts/bootstrap.sh
#
# This script is idempotent — safe to re-run. It will:
#   1. Check prerequisites (uv, git)
#   2. Sync dependencies
#   3. Install pre-commit hooks
#   4. Create .env from .env.example if missing
#   5. Run tests to verify the install
#
# Failure at any step aborts with a clear message.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[bootstrap]${NC} $1"; }
warn() { echo -e "${YELLOW}[bootstrap]${NC} $1"; }
err()  { echo -e "${RED}[bootstrap]${NC} $1" >&2; }

# -----------------------------------------------------------------------------
# 1. Prerequisites
# -----------------------------------------------------------------------------

info "Checking prerequisites..."

if ! command -v git >/dev/null 2>&1; then
    err "git is not installed. Install git first."
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    err "uv is not installed."
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

info "Prerequisites OK."

# -----------------------------------------------------------------------------
# 2. Dependencies
# -----------------------------------------------------------------------------

info "Syncing dependencies with uv..."
uv sync --all-extras --dev

# -----------------------------------------------------------------------------
# 3. Pre-commit hooks
# -----------------------------------------------------------------------------

info "Installing pre-commit hooks..."
uv run pre-commit install

# Initialize secrets baseline if detect-secrets hook needs it
if [ ! -f ".secrets.baseline" ]; then
    info "Initializing detect-secrets baseline..."
    uv run detect-secrets scan --baseline .secrets.baseline || \
        warn "detect-secrets not yet available; baseline will be created on first commit"
fi

# -----------------------------------------------------------------------------
# 4. .env file
# -----------------------------------------------------------------------------

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        info "Creating .env from .env.example..."
        cp .env.example .env
        warn ".env created with placeholder values."
        warn "Edit .env to add your actual API keys before running against live data."
    else
        err ".env.example is missing. Cannot create .env."
        exit 1
    fi
else
    info ".env already exists, not overwriting."
fi

# -----------------------------------------------------------------------------
# 5. Verify
# -----------------------------------------------------------------------------

info "Running tests to verify install..."
uv run pytest -q

info ""
info "Bootstrap complete. Next steps:"
info "  1. Edit .env with your actual API keys"
info "  2. Review docs/BLUEPRINT.md for the full system plan"
info "  3. Review docs/ARCHITECTURE.md for the layered overview"
info "  4. Begin Sprint 0 tasks from CLAUDE.md"
info ""
