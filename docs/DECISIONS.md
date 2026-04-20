# Architecture Decision Records

This log captures decisions that affect the system's architecture. Every meaningful choice — library selection, layer boundary, design pattern — gets a record here. Future-you needs to understand why past-you chose X over Y.

Format: each entry follows the lightweight ADR template below. Newest entries at the top.

---

## Template

```markdown
## ADR-NNN — Short Title

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Context:** What is the issue we're seeing that motivates this decision?
**Decision:** What is the change we're making?
**Consequences:** What becomes easier or harder? What are we accepting?
**Alternatives Considered:** What else did we look at? Why not those?
```

---

## ADR-007 — Cowork Output Drift Monitoring

**Date:** 2026-04-20
**Status:** Accepted
**Context:** ADR-005 places every LLM-mediated task inside Cowork. Cowork's runtime — orchestration logic, skill loading, default tool availability, system prompts, harness behavior — can change without any change to the prompt version or model version we pin. Two lens calls with identical inputs, identical model, and identical prompt can therefore diverge across time. Silent drift of this kind is particularly corrosive to a grading system whose statistical power depends on comparing forward returns against a stable lens output surface. ADR-005 flagged the risk and pointed here for the mitigation; this ADR specifies it.
**Decision:** A monthly regression suite replays a pinned historical corpus of lens inputs (the "anchor corpus") through the currently deployed lens configuration and compares outputs against the last accepted baseline. The comparison measures four surfaces: directional agreement on the primary stance field, distributional shift on the numeric confidence field (Kolmogorov–Smirnov), exact-match accuracy on structured enum fields, and embedding similarity on the free-text falsification field. Results land in `data/research/_drift_reports/YYYY-MM.md`, signed with the orchestration version, model version, and prompt version active at replay time. The anchor corpus itself is fixed at Sprint 6 and may only be replaced — never edited — by a superseding ADR.
**Thresholds and actions:**
- Within declared tolerance on all four surfaces → continue; baseline unchanged.
- Outside tolerance but stable across two consecutive reports → trigger a routing review (ADR-006) and, if the review accepts the new behavior, re-baseline. Re-baselining resets the lens's effective-N counter in the Trial Registry.
- Outside tolerance and unstable → freeze the affected lens's contribution to production grading; human operator decides whether to unfreeze.
**Consequences:**
- Catches silent drift that prompt/model pinning alone cannot catch.
- Adds a fixed monthly regression cost (roughly the size of the anchor corpus × number of deployed lenses).
- Requires the anchor corpus to exist — a Sprint 6 task that blocks full drift monitoring until then. Until Sprint 6, drift is monitored informally via the weekly lens drift cadence in the Cowork brief.
- Re-baselining creates an N-increment in the Trial Registry, which compounds the deflation adjustment applied to downstream Sharpe claims. This is the correct accounting — the lens before and after re-baseline is, for grading purposes, two lenses.
- Drift reports are themselves Cowork artifacts, so the monitor is subject to the thing it monitors. Monthly reports are cross-checked against the previous month's raw replay outputs, which are archived by hash.
**Alternatives Considered:** No monitoring (rejected — ADR-005's entire premise rests on having a mechanism here). Per-call determinism checks (rejected — expensive, and noise on any single call is uninformative). Canary Cowork instance shadowing production (rejected — the Mac Mini is a single point of failure per ADR-005; a canary on the same host shares that failure domain without adding useful signal).

---

## ADR-006 — Model Routing Per Task Type Is a Declared Contract

**Date:** 2026-04-20
**Status:** Accepted
**Context:** Cowork supports selecting Opus 4.6, Sonnet 4.6, or Haiku 4.5 per task. ADR-005 argues this is the primary reason we don't need a separate API path — the cost/quality optimization is already available inside Cowork. That argument only holds if the routing is stable and auditable. If task authors can quietly upgrade a lens from Sonnet to Opus, or downgrade a triage step from Sonnet to Haiku, the grading system conflates "strategy changed" with "model changed" and the Trial Registry's effective-N accounting breaks.
**Decision:** The mapping from task type to model is a versioned contract, declared in the Model Routing table inside `docs/COWORK_BRIEF.md`. The current assignment is: Opus 4.6 for synthesis, thesis writing, and deep research cycles; Sonnet 4.6 as the default, including lens inference and strategy selection; Haiku 4.5 for triage and high-volume classification. Any change to the table is a prompt-version-bumping event for every task it touches and must go through shadow evaluation before being accepted into production. The model version in effect at the time of a call is part of the call's fingerprint (alongside prompt version and input hash) for grading and drift purposes.
**Consequences:**
- Grading is consistent: a lens's score moves only when the lens changes, not when a task author silently reroutes it.
- Routing changes require deliberate experiments, slowing the "just try Opus on this" reflex but producing evidence that a change is actually beneficial.
- New model releases from Anthropic trigger a scheduled shadow evaluation rather than opportunistic rollout. The monthly routing review (Cowork brief cadence) is the venue where escalation rates, refusal rates, and structured-output failures are reviewed and a routing update, if any, is proposed.
- The routing table becomes a small piece of system documentation that must be kept in sync with both the code that calls the models and the grading infrastructure that reads the fingerprint.
- Operator can override routing for ad-hoc investigation, but the override is flagged in the call log and excluded from grading. This preserves experimentation without polluting the production signal.
**Alternatives Considered:** Free choice per task (rejected — destroys grading stability, already explained). Single model everywhere (rejected — foregoes the cost and latency wins available from routing; Haiku on high-volume triage is a real savings). Auto-routing based on input length or detected complexity (rejected for now — adds a second source of routing variation that would itself need grading and versioning; revisit once the manual contract has been in place long enough to produce evidence on what a useful auto-router would do).

---

## ADR-005 — Cowork-Only Architecture, No Direct API Usage

**Date:** 2026-04-20
**Status:** Accepted
**Context:** The initial design had direct Anthropic API calls for production lens inference, with Cowork running only research cycles and operational orchestration. On reflection, three things eliminate the structural reasons to split the LLM layer across runtimes: (a) per-task model routing is declarable inside Cowork (see ADR-006), so the cost/quality optimization the API path would have delivered is already available; (b) a Mac Mini running Claude Desktop 24/7 provides the scheduling reliability the API path was assumed to need; (c) grading is performed against the Cowork-mediated output, not against raw-API reproducibility, so splitting the runtime creates a grading surface we would then have to reconcile for no production benefit.
**Decision:** Cowork is the runtime host for all LLM-mediated work in QuantLab. No direct Anthropic API usage. Lens inference, lens grading, strategy selection, research cycles, thesis writing, digest preparation, and all operational orchestration run as Cowork tasks — scheduled or on-demand. Python scripts handle the deterministic path: data ingestion, backtests, portfolio construction, risk checks, IBKR execution, validation statistics. The two runtimes meet at the handoff directories: Cowork writes structured JSON to `data/cowork_outputs/` (general tasks) and `data/research/lens_outputs/` (lens calls specifically, via the `lens_output` skill). Python reads from those directories and never writes into them. Cowork never writes into `src/`, `tests/`, `scripts/`, or Python-owned `data/` subdirectories.
**Consequences:**
- One billing relationship (Max 20x). Simpler commercial and operational footprint.
- Simpler architecture: one runtime, one orchestrator, one place to find every LLM call.
- Dependent on Mac Mini uptime — single point of failure for the entire LLM layer. Mitigations: UPS, watchdog, cadence-miss logging, monthly failover drill.
- Cowork orchestration updates can drift lens outputs even when prompt versions are pinned. Governed by ADR-007 (Cowork Output Drift Monitoring).
- Lens inference cost is amortized over the Max plan rather than metered per call. Removes a fine-grained cost signal that the API path would have provided for routing decisions. Replaced by the escalation-rate review in the monthly routing cycle.
- All LLM calls are still individually logged (model version, prompt version, input hash, output, timestamp) for grading — Cowork-mediated or not.
**Alternatives Considered:** Hybrid Cowork + API (rejected — adds a second runtime for a cost/quality problem already solved by in-Cowork routing; doubles the grading surface). API-only (rejected — more expensive at current volumes; loses the Cowork orchestration, skills, and scheduled-tasks surface that production research relies on).

---

## ADR-004 — Research Artifacts Under `data/research/`, Not Top-Level

**Date:** 2026-04-20
**Status:** Accepted
**Context:** Layer 12 (Strategy Research Loop) and Layer 13 (Research Assimilation Loop) produce artifacts — paper PDFs, structured paper cards, generated theses, strategy specs, backtests, graveyard records, and (per ADR-005) lens outputs. The original Cowork brief referenced these as top-level directories. The Sprint 0 scaffold did not create them.
**Decision:** Research artifacts live under `data/research/`. Research code stays at `src/quantlab/research/`. Preserves the existing pattern: code in `src/`, data in `data/`, both organized by layer. Cowork's handoff targets for non-research outputs live at `data/cowork_outputs/` (see ADR-005).
**Consequences:**
- Consistent with the existing pattern (`src/quantlab/data/` holds ingestion code; `data/prices/` holds the artifacts).
- `data/research/` subdirectories (`papers/`, `paper_cards/`, `corpus_index/`, `theses/`, `strategies/`, `backtests/`, `graveyard/`, `lens_outputs/`) are created as `.gitkeep` placeholders in Sprint 0 so the paths exist for the `lens_output` skill and the Cowork→Python handoff from day one. Substantive artifacts begin arriving in Sprint 6 when Layers 12–13 come online.
- Cowork operating brief (`docs/COWORK_BRIEF.md`) and `CLAUDE.md` reflect this layout.
**Alternatives Considered:** Top-level `research/` tree (rejected — duplicates the existing `src/`/`data/` split). Under `src/quantlab/research/` as a co-located data tree (rejected — code and data must not co-locate; tests and diffing become noisy).

---

## ADR-003 — Polars as Primary DataFrame Library

**Date:** 2026-04-20
**Status:** Accepted
**Context:** Need a DataFrame library for Layer 1 (data storage) and Layer 2 (features). Pandas is the default but has known performance and memory issues at scale, weak point-in-time semantics, and messy lazy evaluation.
**Decision:** Polars is the primary DataFrame library. Pandas stays in dependencies because a few upstream libraries require it (pandas-market-calendars), but quantlab code uses Polars for all feature computation, storage, and validation.
**Consequences:**
- Faster feature computation, lower memory footprint
- Cleaner lazy evaluation story for as-of-date queries
- Less ecosystem examples to copy — more thinking required
- Team/future contributors need Polars fluency
**Alternatives Considered:** Pandas (legacy choice, weaker for point-in-time); Dask (overkill for single-machine); DuckDB-only (no in-memory DataFrame ergonomics).

---

## ADR-002 — DuckDB for Structured Queries over Parquet

**Date:** 2026-04-20
**Status:** Accepted
**Context:** The data lake stores prices, corporate actions, adjustments, universe as Parquet files. Need a way to run structured queries (e.g., "give me S&P 500 constituents as of date X with their adjusted prices") without loading everything into memory.
**Decision:** DuckDB runs in-process over Parquet files. No server. No ORM. SQL for structured queries, Polars for in-memory transforms.
**Consequences:**
- Zero-configuration, fast, embeddable
- SQL is a lingua franca; queries readable for audit
- Not suitable for concurrent writes (single-writer OK for our use case)
**Alternatives Considered:** SQLite (slower on columnar data), Postgres (heavier ops), direct Polars scans (weaker for complex cross-table queries).

---

## ADR-001 — Polygon.io as Primary Market Data Source

**Date:** 2026-04-20
**Status:** Accepted
**Context:** Need a primary source for daily and intraday bars, corporate actions, options chains. Evaluated FMP, Polygon, Databento, Tiingo.
**Decision:** Polygon.io Developer tier as primary. IBKR native as execution-layer redundant source. Build our own history (see ADR-004 when drafted).
**Consequences:**
- Strong developer ergonomics and API design
- Clean WebSocket streaming if needed later
- US-focused (fine for current universe)
- We own data storage and adjustment logic — more work upfront, more control long-term
- Cost: ~$79-200/month depending on tier
**Alternatives Considered:** FMP (aggregator, weaker data integrity); Databento ($199/mo Standard, institutional-grade but overkill for swing); Tiingo (good historical, thinner options coverage); IBKR-only (rate-limited, not designed for bulk backtest).

---

*End of log. Add new entries at the top.*
