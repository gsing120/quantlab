---
name: lens_output
description: Canonical contract for producing a single lens call. Use whenever running a Rates, Equity Risk, Flow, Geopolitical, Retail Narrative, or Contrarian lens over an event input. Enforces strict JSON schema, deterministic file layout, and an appended log entry for grading. Triggers include any task that says "run the <lens> lens", "score this event through <lens>", or "generate a lens output".
---

# `lens_output` — Canonical Lens Call Contract

Every lens call in QuantLab produces exactly one structured JSON file on disk and exactly one appended line in a log file. Grading, drift monitoring, and Trial Registry accounting all key off this surface — nothing else. If the output doesn't conform to the schema below, the call has failed regardless of whether the reasoning was sensible.

This skill is the only supported path for writing lens outputs. Do not invent ad-hoc paths or schemas.

## Parameters

When a caller invokes this skill, they must provide:

- `lens_id` — one of: `rates`, `equity_risk`, `flow`, `geopolitical`, `retail_narrative`, `contrarian`. Exactly one.
- `regime_context` — compact description of the current market regime (risk-on / risk-off, vol regime, trend regime). Supplied by the orchestrator, not inferred from the event.
- `political_context` — compact description of the political/policy backdrop relevant to the lens.
- `calendar_context` — upcoming scheduled events (FOMC, earnings clusters, auctions, CPI) within the next 10 trading days.
- `event_input` — the event to score: news item, filing, macro release, or market action. Free-form text, but should include a timestamp and source.

If any parameter is missing, **fail loud** — do not proceed with a partial call. A missing `regime_context` in particular silently biases the output.

## Required Output Schema

Produce a single JSON object with **exactly** these 12 top-level fields, in this order:

```json
{
  "lens_id": "rates",
  "prompt_version": "1.0.0",
  "model_version": "claude-sonnet-4-6",
  "orchestration_version": "cowork-2026-04",
  "timestamp_utc": "2026-04-20T14:32:00Z",
  "input_hash": "sha256:...",
  "event_summary": "one-sentence restatement of the event in the lens's own framing",
  "stance": "bullish | bearish | neutral",
  "confidence": 0.00,
  "horizon_days": 10,
  "structured_signals": {
    "primary_factor": "string",
    "secondary_factors": ["string", "..."],
    "affected_universe": ["sector|ticker|all", "..."],
    "regime_conditionality": "string"
  },
  "falsification": "plain-text statement of what observation within horizon_days would prove this stance wrong"
}
```

Field constraints:

- `lens_id` must match the caller's parameter exactly.
- `prompt_version` is the version of this skill/prompt. Bump on any semantic change.
- `model_version` is the model actually used (Cowork surfaces this).
- `orchestration_version` is the Cowork orchestration fingerprint — matters for ADR-007 drift monitoring.
- `timestamp_utc` is ISO 8601 with `Z` suffix.
- `input_hash` is the SHA-256 of the concatenated (lens_id, regime_context, political_context, calendar_context, event_input) inputs. Orchestrator computes this and passes it in; lens echoes it.
- `event_summary` is **one sentence**, ≤ 240 chars, the event as reframed by this lens's perspective.
- `stance` is one of three enum values. No hedging strings like "slightly bullish".
- `confidence` is a float in [0.0, 1.0]. Not a percentage.
- `horizon_days` is an integer in [1, 20]. Matches the system's swing horizon.
- `structured_signals.primary_factor` is a single dominant driver (e.g. "duration risk", "liquidity squeeze", "positioning crowded").
- `structured_signals.secondary_factors` is a list of 0–4 additional drivers. Not a dumping ground.
- `structured_signals.affected_universe` is a list of tickers, sector codes (GICS L1), or the literal string `"all"`.
- `structured_signals.regime_conditionality` states the regime under which this call holds (e.g. "valid while VIX < 25 and 10Y realized vol < 12%").
- `falsification` is a plain-text, **testable** proposition. "The market goes down" is not testable. "SPX closes below 4850 within 10 trading days" is.

No other top-level fields are permitted. The lens call fails if any are present or missing.

## File Layout

Write the output JSON to:

```
data/research/lens_outputs/YYYY-MM-DD/<lens_id>_<timestamp_utc_compact>.json
```

Where `YYYY-MM-DD` is the UTC calendar date of the call, and `timestamp_utc_compact` is `YYYYMMDDTHHMMSSZ` from the `timestamp_utc` field. Example:

```
data/research/lens_outputs/2026-04-20/rates_20260420T143200Z.json
```

Then append one line to:

```
data/research/lens_outputs/_log.jsonl
```

The log line is a JSON object with: `timestamp_utc`, `lens_id`, `prompt_version`, `model_version`, `orchestration_version`, `input_hash`, `stance`, `confidence`, `output_path`. This is what the drift monitor and Trial Registry consume. Never skip it.

## Validation and Failure Handling

Before writing to disk, validate the output against the schema above. If validation fails:

1. Retry **once** with the schema violation quoted back in the prompt.
2. If the retry still fails, **fail loud**: write nothing, append a `_log.jsonl` entry with `"status": "validation_failed"` and the offending output inline, and raise. Do not quietly coerce, truncate, or default values.

Silent coercion is worse than a visible failure. A missing `falsification` field that gets filled with an empty string will poison grading for weeks before anyone notices.

## What This Skill Does Not Do

- Does not select which lens to call. The orchestrator decides.
- Does not write to `src/`, `tests/`, `scripts/`, or any Python-owned `data/` subdirectory. Only `data/research/lens_outputs/`.
- Does not produce trading signals. Lens outputs are features; the statistical layer produces signals (see CLAUDE.md rule #2).
- Does not read prior lens outputs or look up its own history. Every call is independent; history lives in the log file for the grading layer to consume.

## References

- ADR-005: Cowork-Only Architecture (`docs/DECISIONS.md`)
- ADR-006: Model Routing Per Task Type Is a Declared Contract (`docs/DECISIONS.md`)
- ADR-007: Cowork Output Drift Monitoring (`docs/DECISIONS.md`)
- Cowork operating brief: `docs/COWORK_BRIEF.md`
