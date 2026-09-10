# Decision Memo: Should the First Gate Move from Level 30 to Level 40?

To: Cookie Cats game and product team
From: Aishwary Srivastava
Date: 2026-09-10

## Recommendation

**Keep the first gate at level 30.** Moving it to level 40 lowered 7-day retention by
0.82 percentage points (a 4.3% relative drop), the result is statistically significant and
holds up under every robustness check we ran, and nothing in the engagement data offsets it.

## Key findings

1. **D7 retention (primary metric) fell.** 19.02% for gate_30 versus 18.20% for gate_40:
   a difference of **-0.82 pp** (-4.3% relative), 95% CI **-1.33 to -0.31 pp**, p = 0.0016.
   It stays significant after Holm correction for having tested two metrics (adjusted p = 0.0031).
2. **D1 retention moved the same way but is inconclusive.** -0.59 pp, 95% CI -1.24 to +0.06 pp,
   p = 0.074. The interval crosses zero, so we cannot rule out "no effect" - but we also cannot
   rule out a drop of up to 1.24 pp. It is not evidence that D1 is unaffected.
3. **Three independent methods agree with the D7 result.** Bootstrap 95% CI -1.34 to -0.31 pp
   (gate_30 came out ahead in 99.9% of 10,000 resamples); permutation test p about 0.0016
   (0.00162 from two million shuffles); Bayesian Beta-Binomial probability that gate_40 is truly
   better: **about 0.1%**, with an expected loss of 0.82 pp of D7 retention if we ship it against
   essentially 0.00 pp if we keep gate_30.
4. **Engagement did not meaningfully change.** The apparent gap in mean rounds played
   (-1.16 rounds) came almost entirely from one physically impossible value; without it the gap is
   -0.04 rounds (p = 0.95). The rank-based Mann-Whitney test is borderline (p = 0.0502) with a
   negligible effect size (probability of superiority 0.4962). The one visible pattern is *where*
   players stop: gate_30 players cluster just after 30 rounds.

## Why this matters for the business

Out of every **10,000 new players, about 82 fewer come back to play on day 7** under gate_40.
Week-one retention is the top of every later funnel - sessions, ad impressions and purchases all
scale off the players still present on day 7 - so a 4.3% relative loss there compounds through the
rest of the player lifetime. The change also has no upside to trade against: rounds played are
statistically indistinguishable between the versions.

## Validity and data quality

- **Sample ratio mismatch: borderline.** gate_40 received 789 more players than gate_30
  (45,489 vs 44,700). Against an assumed 50/50 design that is chi-square p = 0.0086: flagged at the
  0.05 and 0.01 thresholds, **not** flagged at the 0.001 threshold most experimentation platforms
  alarm on. The imbalance is spread evenly across userid deciles rather than concentrated in one ID
  range, and the intended allocation ratio is not documented anywhere in the data. We report the
  result and recommend checking assignment logs; we do not discard the test.
- **One physically impossible rounds value.** A single gate_30 player logged 49,854 rounds -
  about 3,561 per day even over a 14-day window, against a ceiling of 2,880 per day at 30 seconds
  per round with no breaks. It was **flagged, not deleted**: kept in the retention analysis
  (intention-to-treat) and reported with and without in the engagement analysis.
- **111 players with zero rounds are marked as retained.** Retention is described as "came back and
  played", so these rows are internally inconsistent. The count is nearly identical in both groups
  (56 gate_30, 55 gate_40), so it is unlikely to bias the comparison, but it is a logging issue
  worth fixing.

## A hypothesis worth testing (clearly labelled as a hypothesis)

A gate at level 30 forces an earlier break. That break may keep players from burning out and give
them a reason to come back the next day, which would explain the higher D7 retention.
**This dataset cannot test that explanation.** A follow-up test with different wait times, or data
on when players return, could.

## Limitations

- The intended allocation ratio is not documented, so the SRM check rests on assuming 50/50.
- **No revenue or purchase data**, even though gates exist partly to drive purchases. A retention
  win and a monetization win are not the same decision.
- The measurement window for `sum_gamerounds` is not clearly documented (one week or 14 days,
  depending on the source).
- No install dates, so time trends and novelty effects cannot be checked.
- No player attributes measured before assignment, so no fair segment analysis is possible; rounds
  played cannot be used for this, because filtering on it more than doubles the apparent effect
  (-1.78 pp vs the valid -0.82 pp).
- The test could reliably detect only D7 changes of about **0.73 pp or larger** at 80% power.
  Detecting the 0.5 pp threshold we set as practically meaningful would need about 95,700 players
  per group.

## Suggested next steps

- Measure revenue and purchase conversion by version before making any final monetization decision.
- Track retention beyond day 7 (D14 and D30) to see whether the gap widens or closes.
- Investigate the SRM with assignment and logging data, and fix the zero-rounds-but-retained rows.
- If the team still wants a later gate, test an intermediate option such as level 35, sized in
  advance for a 0.5 pp MDE (about 95,700 players per group, roughly 32 days at 3,000 new players
  per group per day).

## Chart

![Retention difference with 95% CI](figures/05_retention_diff_ci.png)
