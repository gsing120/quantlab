# QuantLab Blueprint

Full implementation specification for the 13-layer multi-lens swing trading system.

Companion docs: [`ARCHITECTURE.md`](./ARCHITECTURE.md) for concise overview, [`DECISIONS.md`](./DECISIONS.md) for ADR log, [`QUESTIONS.md`](./QUESTIONS.md) for open questions.

---

## Part I — System Philosophy & Non-Negotiables

### Core Principles

**The system exists to measure edge honestly, not to generate confident predictions.** Every component either produces a testable signal or grades signals against reality. Nothing exists to "look smart" or generate plausible-sounding output without accountability.

**Deterministic money path, probabilistic intelligence layer.** Code that touches capital is hard-coded, tested, version-controlled. LLM reasoning is structured, logged, graded. The two paths are architecturally separate and meet only at the feature store.

**Continuous grading, gated promotion.** Nothing changes in production based on point estimates. Shadows must accumulate statistical evidence of improvement in the conditions where they'd be deployed. Promotion is cell-by-cell, not monolithic.

**Swing horizon: 5–20 trading days.** All features, labels, validation, and execution are tuned to this holding period.

### Hard Rules (Never Violate)

1. No real capital until paper trading matches backtest within acceptable tolerance for minimum 3 months.
2. No LLM output directly generates orders. LLM outputs become features; statistical models decide.
3. Every LLM call logged with model version, prompt version, input, output, timestamp. No exceptions.
4. Every piece of historical data has two timestamps: what-it-refers-to and when-we-learned-it.
5. No shadow promoted without minimum sample size, statistical significance corrected for multiple testing, cross-regime stability.
6. No backtest trusted until cross-validated against Ken French published factor returns.
7. Max single position: 3%. Max sector: 25%. Max gross exposure: 150%.
8. Circuit breakers: hard stop on 10% drawdown from peak, mandatory review before reactivation.

---

## Part II — The 13-Layer Architecture

### Layer 1: Data Infrastructure
Polygon API client (primary), IBKR native (execution-layer real-time). Parquet storage with four parallel stores. Point-in-time universe tracking. Exchange calendar integration. `instrument_id` as primary key.

### Layer 2: Numerical Features
Versioned registry. Cross-sectional, time-series, fundamental, microstructure. Pure functions of `(panel, as_of_date)`.

### Layer 3: Semantic Features

**3a — Event Ingestion & Decomposition:** news, SEC EDGAR, Fed, earnings transcripts, Reddit, Twitter/X, FRED.

**3b — Source Reputation:** four-tier taxonomy (Primary / Professional / Social-Alt / Aggregator), per-source and per-author conditional scores, coordinated-activity detection, origin tracking.

**3c — Lens Agents (parallel):** Rates, Equity Risk, Flow/Positioning, Geopolitical Second-Order, Retail Narrative, Contrarian/Regime-Break. Structured outputs, pinned model versions, pinned prompt versions.

**3d — Dispersion & Consensus:** agreement across lenses as standalone feature. High dispersion → larger realized volatility.

**3e — Regime-Gated Weighting:** current regime × political × calendar → active lens set via conditional performance lookup.

**3f — Continuous Grading:** every lens output logged and graded against forward returns. Bayesian running estimates. Deflated Sharpe corrections.

### Layer 4: Labels
Triple-barrier labeling with ATR-scaled barriers. Time barrier 10–15 days. Costs embedded. Purging and embargo for overlapping labels.

### Layer 5: Regime Classifier
Numerical indicators (vol, correlations, breadth, term structure) + semantic regime signals (lens consensus breaks). HMM + Statistical Jump Model as independent opinions. Disagreement as regime-uncertainty feature.

### Layer 6: Model Ensemble
Momentum, mean-reversion, quality/value sub-models. Each trained on its native regime. Regime-gated weighting or meta-learner. Semantic features as first-class inputs.

### Layer 7: Validation
**Combinatorial Purged CV** (not Purged K-Fold). Combinatorial CPCV for hyperparameter search. Walk-forward with explicit refit cadence. Regime-stratified evaluation. Deflated Sharpe with ONC-adjusted effective trial count. **Ken French cross-validation (>0.9 correlation) required** before trusting any pipeline result.

### Layer 8: Portfolio Construction & Risk
Signal-to-weight via fractional Kelly with volatility targeting. Constraint layer (per-name, sector, factor, gross/net). Correlation-adjusted sizing. Gap-risk model. Transaction cost model. Event-risk filtering. Pre-trade Claude sanity check.

### Layer 9: Execution
`ib_insync` with connection management. State machine with idempotent rebalancing. VWAP/TWAP for larger orders. Daily reconciliation.

### Layer 10: Model Version Management
Continuous shadow training. Promotion gates: sample size, significance, stability, no adverse selection. Cell-by-cell migration. Graveyard for retired shadows.

### Layer 11: Orchestration
- **Claude Code:** development and maintenance
- **Cowork:** scheduled workflows, research cycles, daily operations
- **Claude API (direct SDK):** production lens inference — only path producing trading features
- **Human-in-loop:** thesis review, promotion approvals, capital gates

### Layer 12: Strategy Research Loop
Paper acquisition → topic landscape → multi-agent synthesis → integrated thesis → strategy derivation → triage → controlled backtest → shadow slot → gated promotion.

**Guards (mandatory):**
- Evidence provenance (every claim cites sources)
- Own-thesis contamination limit (≤20% self-generated material)
- Periodic first-principles rebaselining (every N cycles)
- Adversarial cycles (every M cycles, attack the house view)
- Global trial count for Deflated Sharpe
- Human thesis review before strategy derivation
- Citation verification (automated)
- Replication attempts on key source papers

### Layer 13: Research Assimilation Loop
Research ingestion → human triage → shadow test → promotion decision → technique register. Same promotion discipline as lens/strategy shadows.

---

## Part III — Implementation Sprints

### SPRINT 0 — Foundation Setup (~3 days)

Project structure, dependencies, CI, logging, config, secrets. Full checklist in [`CLAUDE.md`](../CLAUDE.md).

**Gate:** Fresh clone → `uv sync` → `pytest` all green → pre-commit hooks enforce → `.env.example` complete → all docs in place.

### SPRINT 1 — Statistical Core (Weeks 1–3)

Layer 1 (Polygon + storage + universe), basic Layer 2 (momentum, reversal, vol, liquidity), Layer 4 (triple-barrier), minimal Layer 7 (purged CV, Deflated Sharpe, walk-forward), baseline Layer 6 (LightGBM).

**Gate:** Baseline model produces Sharpe ≥0.5 after realistic costs on OOS walk-forward, Ken French correlation check ≥0.9. **No Sprint 2 work begins before this gate.**

### SPRINT 2 — Multi-Signal Statistical (Weeks 4–6)

Expanded Layer 2 (fundamentals, quality, value, options-derived). Layer 5 (HMM + SJM). Layer 6 ensemble. Layer 7 enhanced (CPCV, regime-stratified). Layer 8 portfolio construction.

**Gate:** Portfolio Sharpe ≥0.7 after costs OOS, stable across regimes (no single regime >60% of returns), measurable residual alpha after factor exposure.

### SPRINT 3 — First Semantic Layer (Weeks 7–10)

Layer 3a (event ingestion). Layer 3c with **two lenses only** (Rates + Retail Narrative). Layer 3f (grading infrastructure). Historical replay validation.

**Gate:** At least one lens demonstrates statistically significant edge contribution, OR clear diagnostic on why. **If no lens adds edge, redesign before adding more.**

### SPRINT 4 — Full Lens System (Weeks 11–14)

Layer 3b (source reputation). Remaining four lenses. Layer 3d (dispersion). Layer 3e (regime-gated weighting). Cowork orchestration. Knowledge layer.

**Gate:** System Sharpe improvement over Sprint 2 is measurable and significant.

### SPRINT 5 — Paper Trading (Months 4–6+, minimum 3 months)

IBKR paper account, full execution state machine, real-time monitoring, daily reconciliation, continuous live grading, pre-execution review loop.

**Gate for real capital:** 3+ months paper, paper Sharpe within tolerance of backtest, no unresolved execution failures, drawdown within envelope, lens grades stable, human reviewer confident.

### SPRINT 6 — Research Assimilation Loop (Weeks 15–18, post paper-trading)

Layer 13 infrastructure. Research ingestion. Triage workflow. Shadow test harness. Technique register.

### SPRINT 7 — Paper Corpus Foundation (Weeks 19–22)

Paper ingestion pipeline. Grading agent. Embeddings. Topic clustering. Landscape tracking.

### SPRINT 8 — Deep Research Cycle MVP (Weeks 23–27)

Full multi-agent cycle at low frequency (monthly). Every thesis reviewed by human. Goal: prove the cycle produces coherent, well-cited, useful theses before deriving strategies.

### SPRINT 9 — Strategy Derivation (Weeks 28–31)

Only after Sprint 8 produces reliable theses. Derive strategies, run through existing triage/backtest/shadow gates.

### SPRINT 10+ — Scaling & Guards (Ongoing)

Adversarial cycles. Rebaselining protocol. Citation verifier. Graveyard learning. Frequency scaling.

---

## Part IV — The Research Factory (Layer 12 Detail)

### Pre-work: Ingestion & Corpus

Daily scan: arXiv q-fin/cs.LG/stat.ML, SSRN finance, Journal of Finance / JFE / RFS, Journal of Financial Data Science, NeurIPS/ICML/ICLR finance tracks, curated researcher feeds. Paper grading agent produces structured evaluation. Grading includes **negative results and replication failures** — not just successes. Corpus is versioned, embedded, topic-clustered, citation-linked.

### Deep Research Cycle (one cycle = one integrated thesis)

1. **Topic selection and scoping** — landscape agent selects cluster, orchestrator frames specific testable question, question logged immutably (pre-registration).

2. **Paper deep-reading** — 10–30 most relevant papers retrieved. Reader agent extracts claim, setup, data/time-period, acknowledged limitations, unacknowledged limitations (adversarial pass), causal mechanism. Stored as paper card.

3. **Cross-paper analysis** — synthesis agent produces agreements, disagreements and their sources, unexplored combinations, gaps.

4. **Adversarial review** — red-team agent attacks the draft. Findings incorporated or rebutted.

5. **Integrated thesis** — structured research document with specific claim, evidence base, novel contribution, predictions distinguishing this thesis from components, falsification conditions, proposed empirical tests.

6. **Strategy derivation** — strategy agent takes thesis, produces hypothesis per Layer 12 schema. Full lineage preserved.

7. **Testing pipeline** — strategy enters triage → controlled backtest → shadow slot.

### The Recursive Ingredient

Prior theses become input to future cycles. **Guarded heavily:**

- Each cycle can cite ≤20% self-generated material
- Every N cycles: "blank slate" rebaseline (no prior theses as input)
- Every M cycles: adversarial cycle attacks house view
- Citation verification automated
- Human reads every thesis before strategy derivation

---

## Part V — Critical Risks & Mitigations

**Data Risks**
- Corporate action errors → cross-validation against second source; manual audit
- Survivorship bias → point-in-time universe, delisting records
- Lookahead leakage → strict `as_of_date` enforcement, unit tests per feature
- Data revisions → store originals with `ingested_at`; backtests use originals, live uses latest

**Model Risks**
- Overfitting → CPCV, Deflated Sharpe, OOS gates
- Regime change → classifier, sub-models, shadows
- Factor crowding → decomposition, monitor residual alpha
- Feature decay → continuous grading, retirement criteria

**LLM-Specific Risks**
- Model version drift → pinning, historical replay on upgrades
- Prompt sensitivity → versioning, A/B on shadows
- Hallucinated features → structured outputs, grading against reality
- Systematic biases → lens diversity, dispersion signal, human review
- Cost explosion → rate limiting, caching, right-sized model per task

**Execution Risks**
- Broker outages → manual fallback procedures
- Order routing errors → idempotent state machine
- Slippage worse than modeled → continuous tracking
- Gap risk → event calendar filtering, overnight vol model

**Research Loop Risks**
- Elegant-but-wrong theses → human thesis review mandatory
- Echo chambers → self-contamination limit + rebaselining cycles
- Fabricated citations → automated verification
- Multiple-testing trap → global trial count across all shadows

**Strategic Risks**
- Chasing noise → shadow-first discipline
- Scope creep → sprint gates
- Premature scaling → start small
- Emotional override → hard rules, circuit breakers

---

## Part VI — Success Criteria

**Minimum Viable (Sprint 2 complete)**
- Sharpe ≥0.7 after costs, OOS walk-forward
- Max drawdown <15%
- Stable across regimes
- Residual alpha after factor exposure

**Full System (Sprint 5 paper trading)**
- Sharpe ≥1.0 after costs
- Max drawdown <12%
- Paper-vs-backtest within 20% Sharpe tolerance
- At least one lens demonstrating edge

**Live Year 1**
- Sharpe ≥0.8 after all costs including taxes
- Max drawdown <15%
- Capacity >$1M demonstrated
- P&L attribution matches expected contributions

**Maturity (Year 2+)**
- Multiple lens versions promoted via shadows
- ≥1 successful LLM migration via parallel evaluation
- Stable performance across regime transitions
- Research pipeline producing validated new signals quarterly

---

## Part VII — Anti-Patterns to Avoid

1. Adding complexity before validating current layer
2. Trusting backtest without Ken French validation
3. Promoting shadows on point estimates
4. Using LLM output as direct trade signal
5. Skipping paper trading "because backtest looks great"
6. Building an aggregator when you need an LLM interpreter
7. Over-engineering before shipping
8. Confusing activity with progress
9. Ignoring transaction costs
10. Emotional override of the system
11. TSFMs for daily return prediction (use only for vol/volume covariates)
12. 1M-token contexts as a substitute for retrieval (multi-fact recall drops beyond 500K)
13. Chain-of-Thought on reasoning models (use `effort` parameter instead)
14. Verbalized confidence as primary calibration signal (use self-consistency)
15. Full GraphRAG at retail scale (use LazyGraphRAG or HippoRAG 2 if needed)
16. Fine-tuning for open-ended reasoning (frontier base models subsume you)
17. Bandit optimization on P&L (use bandits on proxy metrics, A/B on P&L)
18. Unbounded agent autonomy (always set max_iterations, max_tokens, max_wall_clock)

---

## Part VIII — The Meta-Discipline

- **Measure before believing.** Every edge claim grounded in OOS evidence.
- **Build incrementally.** Each sprint proves its piece before the next begins.
- **Grade continuously.** Every component is an instrument requiring calibration.
- **Promote rigorously.** Statistical significance, cross-regime stability, no adverse selection.
- **Log everything.** Without logs, no diagnosis, no grading, no improvement.
- **Review honestly.** If something isn't working, diagnose it, fix it, or kill it.

The architecture helps keep discipline. When discipline fails, no architecture saves you. When discipline holds, this architecture gives every advantage a retail operator can reasonably have.

---

*Blueprint version 1.0. Status: Pre-Sprint 0. Next milestone: Sprint 0 completion, Sprint 1 kickoff.*
