# QuantLab Architecture

A concise map of the 13-layer system. For the full blueprint with sprint plans, risks, success criteria, and implementation checklists, see [`BLUEPRINT.md`](./BLUEPRINT.md).

## System Philosophy

**The system exists to measure edge honestly, not to generate confident predictions.**

Two separate paths run through every component:

- **Deterministic money path.** All code touching capital — position sizing, order generation, risk checks, execution — is hard-coded, version-controlled, tested Python.
- **Probabilistic intelligence layer.** All LLM-based reasoning — lenses, semantic features, source grading, research synthesis — is structured, logged, graded, and treated as an instrument requiring calibration.

These paths meet only at the feature store. LLM outputs become features; statistical models decide trades.

## The 13 Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 11: Orchestration (Cowork + Claude Code + API + human-in-loop)│
├─────────────────────────────────────────────────────────────────────┤
│  Layer 13: Research Assimilation Loop                                │
│  Layer 12: Strategy Research Loop (Deep Research Cycles)             │
│  Layer 10: Model Version Management (shadow training, promotion)     │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 9:  Execution (IBKR state machine)                            │
│  Layer 8:  Portfolio Construction & Risk                             │
│  Layer 7:  Validation (CPCV, Deflated Sharpe, walk-forward)          │
│  Layer 6:  Model Ensemble (regime-gated sub-models)                  │
│  Layer 5:  Regime Classifier (HMM + Statistical Jump Model)          │
│  Layer 4:  Labels (triple-barrier, meta-labels)                      │
│  Layer 3:  Semantic Features (multi-lens agents)                     │
│  Layer 2:  Numerical Features (pure functions of as_of_date)         │
│  Layer 1:  Data Infrastructure (Polygon + IBKR + Parquet)            │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer 1 — Data Infrastructure
Polygon API client for primary data, IBKR native for execution-layer real-time. Parquet storage with `prices/`, `corporate_actions/`, `adjustments/`, `universe/` stores. Point-in-time correctness enforced: every bar carries `ingested_at`; `instrument_id` as primary key, not ticker.

### Layer 2 — Numerical Features
Versioned feature registry. Cross-sectional (z-scored), time-series (backward-looking only), fundamental, microstructure. All features are pure functions of `(panel, as_of_date)` — lookahead prevented by construction.

### Layer 3 — Semantic Features (Multi-Lens)
Six Claude lenses in parallel: Rates, Equity Risk, Flow/Positioning, Geopolitical Second-Order, Retail Narrative, Contrarian/Regime-Break. Each produces structured output. Dispersion across lenses is itself a feature. Source reputation system grades news/social sources by tier and condition. Continuous grading against forward returns.

### Layer 4 — Labels
Triple-barrier labeling with ATR-scaled barriers. Time barrier matches swing horizon (10–15 days). Transaction costs embedded. Meta-labels for sample weighting.

### Layer 5 — Regime Classifier
HMM baseline + Statistical Jump Model as second opinion. Disagreement between them is a regime-uncertainty feature. Consumes numerical and semantic regime signals. Outputs probability distribution.

### Layer 6 — Model Ensemble
Sub-models per signal class (momentum, mean-reversion, quality/value). Regime-gated weighting. Cross-lens agreement as meta-feature. LightGBM primary, TabPFN v2.5 for ensemble.

### Layer 7 — Validation
Combinatorial Purged CV (CPCV) — not Purged K-Fold. Deflated Sharpe with ONC-adjusted effective N. Regime-stratified evaluation. Cross-validation against Ken French factor returns (>0.9 correlation required before trusting any pipeline result).

### Layer 8 — Portfolio Construction & Risk
Fractional Kelly sizing with volatility targeting. Constraints: 3% per-name, 25% per-sector, 150% gross. Correlation-adjusted sizing. Gap-risk model using empirical overnight vol. Event-filtering (no positions into scheduled earnings without explicit override).

### Layer 9 — Execution
`ib_insync` client. State machine: `target_positions → current_positions → order_diff → execution`. Idempotent rebalancing — crash-safe. Daily reconciliation of backtest-expected vs. live-actual.

### Layer 10 — Model Version Management
Continuous shadow training. Promotion requires minimum sample size, statistical significance (corrected for multiple testing), cross-regime stability, no adverse selection. Cell-by-cell migration — different model versions can own different condition cells.

### Layer 11 — Orchestration & Infrastructure
- **Claude Code** for development and maintenance
- **Cowork agents** for scheduled workflows, research cycles, operational coordination
- **Claude API (direct SDK)** for production lens inference — the only path producing trading features
- **Human-in-loop** for thesis review, promotion approvals, capital deployment gates

### Layer 12 — Strategy Research Loop
Deep Research Cycles: paper acquisition → topic landscape → multi-agent synthesis → integrated thesis → strategy derivation → triage → controlled backtest → shadow slot → gated promotion. Runs monthly at low frequency initially.

### Layer 13 — Research Assimilation Loop
Ingests new academic papers, model releases, and novel techniques. Triage → shadow test → decision. Methodology upgrades enter the system the same way strategies do: only after passing statistical gates.

## Hard Rules (Never Violated)

1. No real capital until paper trading matches backtest within tolerance for minimum 3 months.
2. No LLM output directly generates orders.
3. Every LLM call logged with model version, prompt version, input, output, timestamp.
4. Every piece of historical data has two timestamps: what-it-refers-to and when-we-learned-it.
5. No shadow promoted without sample size, statistical significance, cross-regime stability.
6. No backtest trusted until Ken French factor cross-validation passes.
7. Max 3% per position, 25% per sector, 150% gross exposure.
8. Hard stop at 10% drawdown — mandatory human review before reactivation.

## Data Flow

```
[External]
  Polygon API ────────────────→ Layer 1 (structured store)
  IBKR native ────────────────→ Layer 1 (live prices)
  News / SEC / Fed ───────────→ Layer 3a (raw events)
  Social / FRED ──────────────→ Layer 3a (social + macro)

[Processing]
  Layer 1 ────────────────────→ Layer 2 (numerical features)
  Layer 3a → Layer 3b ────────→ Layer 3c (lens agents)
  Layer 3c ───────────────────→ Layer 3d (dispersion metrics)
  Layer 2 + Layer 3d ─────────→ Layer 5 (regime classification)
  Layer 5 ────────────────────→ Layer 3e (lens weighting)
  Layer 2 + Layer 3 ──────────→ Layer 4 (labels)

[Decision]
  All features + Layer 5 ─────→ Layer 6 (model ensemble)
  Layer 6 ────────────────────→ Layer 8 (portfolio)
  Layer 8 ────────────────────→ Layer 9 (execution)

[Learning]
  Layer 9 outcomes ───────────→ Layer 3f (grading)
  Layer 3f ───────────────────→ Layer 10 (shadow evaluation)
  Layer 10 ───────────────────→ Layer 3c / Layer 6 (promotions)

[Research]
  Papers / releases ──────────→ Layer 13 (assimilation)
  Landscape + empirics ───────→ Layer 12 (strategy research)
  Layer 12 strategies ────────→ Layer 6 (shadow slots)
  Layer 13 techniques ────────→ Any relevant layer (as shadow)
```
