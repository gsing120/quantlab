# notebooks/

Exploratory analysis and scratch work. Not imported by production code.

## Conventions

- Notebooks live in `notebooks/`. Output data goes to `notebooks/output/` (gitignored).
- Clear all outputs before committing (`jupyter nbconvert --clear-output --inplace`)
- Prefer one notebook per investigation; don't let them grow into unreadable monoliths
- When a notebook produces a useful utility, extract it into `src/quantlab/` with tests
- Ruff ignores print statements here (`T20`)
