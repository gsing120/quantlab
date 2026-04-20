# scripts/

One-off and CLI scripts. Nothing here should be imported by `src/quantlab/`.

## Contents

- `bootstrap.sh` — one-command setup for a fresh clone

## Conventions

- Scripts may use `print()` (ruff ignores `T20` in this directory)
- Always make shell scripts executable (`chmod +x`) and include a shebang
- Python scripts should be runnable via `uv run python scripts/<name>.py`
- Long-running scripts should use structured logging from `quantlab.logging`
