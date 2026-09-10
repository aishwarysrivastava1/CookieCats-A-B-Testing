# Pre-Analysis Plan: Cookie Cats Gate Position Test

Date written: 2026-09-10
Author: Aishwary Srivastava

## 1. Background
Cookie Cats players reach gates that force them to wait or pay to continue.
A test randomly assigned new players to a first gate at level 30 (control, current)
or level 40 (treatment). The team may have expected that letting players go 10 levels
further before the first forced stop would feel less restrictive and keep more of them
playing. A later gate also delays the first paid-unlock prompt, so the test is as much
about pacing as it is about monetization.

## 2. Research question
Does moving the first gate from level 30 to level 40 change player retention?

## 3. Hypotheses (two-sided)
- H0: D7 retention is the same for gate_30 and gate_40.
- H1: D7 retention differs between gate_30 and gate_40.
(The same structure applies to D1 retention.)

## 4. Metrics
- Primary metric: D7 retention (`retention_7`). Reason: coming back a week after install
  is a sign that a play habit is forming, which is closer to long-term value than a single
  next-day visit. D1 mostly measures the first impression.
- Secondary metric: D1 retention (`retention_1`).
- Engagement metric: game rounds (`sum_gamerounds`). Used to understand behavior,
  not to make the ship decision.

## 5. Population and unit of analysis
- Unit of randomization and analysis: player.
- Population: all players in the dataset (intention-to-treat). No player is removed
  from retention analysis.

## 6. Statistical settings
- Significance level: alpha = 0.05, two-sided.
- Target power for planning: 80%.
- Practical significance threshold: an absolute change of 0.5 percentage points in D7
  retention. Reason: on a baseline near 19%, 0.5 pp is a ~2.6% relative move in the
  week-one player base. Anything smaller is not worth the engineering, QA and
  player-confusion cost of changing a live progression system.
- Multiple testing: D7 is the single primary metric. D1 results are reported with
  Holm-adjusted p-values.

## 7. Validity checks (run before any outcome analysis)
- Sample ratio mismatch: chi-square goodness-of-fit test against an assumed 50/50 split.
  p < 0.001 = SRM flagged; 0.001 <= p < 0.01 = borderline, report and investigate.
- Data quality: check for missing values, duplicate players, impossible values.
  Physically impossible values will be flagged, not deleted. Engagement analysis will be
  run with and without them.

## 8. Planned analyses
1. Two-proportion z-test and 95% confidence interval for D7 (primary) and D1 (secondary).
2. Robustness checks: chi-square test, bootstrap CI, permutation test, Bayesian
   Beta-Binomial analysis.
3. Engagement: Mann-Whitney U test, Welch's t-test with and without flagged values,
   bootstrap CI for the median difference, winsorized means.

## 9. Decision rule
- If gate_40 D7 retention is significantly LOWER (95% CI entirely below 0): keep the gate at level 30.
- If gate_40 D7 retention is significantly HIGHER (95% CI entirely above 0): recommend moving the
  gate to level 40, after checking engagement results.
- If the result is not significant: keep the gate at level 30 (the current version), because
  changing the game has costs, and report the range of effects the data cannot rule out.

## 10. Known limitations before analysis
- The intended allocation ratio is not documented.
- The measurement window for game rounds is not clearly documented.
- No revenue, install date or player attribute data.
