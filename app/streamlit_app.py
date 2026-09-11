# streamlit_app.py
# Cookie Cats A/B test: an interactive walkthrough of the whole analysis.
# Run locally with:  streamlit run app/streamlit_app.py
#
# The app depends only on files that are committed to the repository:
#   data/processed/summary_by_version.csv   (four numbers per group)
#   reports/figures/*.png                   (the 11 charts the notebooks produced)
# Everything else is either recomputed live from those counts or stored below as a
# constant taken from the executed notebooks, so the deployed app never needs the raw data.

import numpy as np                                   # maths and random numbers
import pandas as pd                                  # tables
import matplotlib.pyplot as plt                      # charts drawn live in the app
import streamlit as st                               # the web app framework
from scipy import stats                              # distributions and statistical tests
from pathlib import Path                             # file paths that work locally and on Streamlit Cloud

# ----------------------------------------------------------------------------------
# Paths and page setup
# ----------------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent            # folder that contains this file (app/)
ROOT = APP_DIR.parent                                # repository root
SUMMARY_FILE = ROOT / "data" / "processed" / "summary_by_version.csv"   # written by notebook 04
FIG_DIR = ROOT / "reports" / "figures"               # the 11 charts saved by the notebooks

st.set_page_config(page_title="Cookie Cats A/B Test", page_icon="🍪", layout="wide")   # tab title, icon, wide layout

# ----------------------------------------------------------------------------------
# Design tokens
# Two series only: control and treatment. The pair is fixed, never swapped, and was
# checked for colour-vision safety (all-pairs CVD delta-E 24.7, contrast >= 3:1 on the
# chart surface), so identity never depends on colour alone - every chart also labels.
# ----------------------------------------------------------------------------------
C_CONTROL = "#2a78d6"                                # gate_30, control
C_TREAT = "#eb6834"                                  # gate_40, treatment
C_SURFACE = "#fcfcfb"                                # chart surface
C_INK = "#0b0b0b"                                    # primary text
C_INK_SOFT = "#52514e"                               # secondary text
C_GRID = "#e3e3de"                                   # recessive grid
C_GOOD = "#007a4d"                                   # status: good
C_WARN = "#b06000"                                   # status: warning
C_BAD = "#c0392b"                                    # status: serious

st.markdown(
    f"""
    <style>
      .hero {{
          background: linear-gradient(135deg, {C_CONTROL}12 0%, {C_TREAT}12 100%);
          border: 1px solid {C_CONTROL}33; border-radius: 14px;
          padding: 1.1rem 1.4rem; margin-bottom: 0.9rem;
      }}
      .hero h2 {{ margin: 0 0 .35rem 0; font-size: 1.35rem; }}
      .hero p  {{ margin: 0; color: {C_INK_SOFT}; font-size: .95rem; line-height: 1.5; }}
      .card {{
          border: 1px solid #e6e6e1; border-radius: 12px; padding: .85rem 1rem;
          background: {C_SURFACE}; height: 100%;
      }}
      .card .lab {{ color: {C_INK_SOFT}; font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; }}
      .card .val {{ font-size: 1.5rem; font-weight: 650; color: {C_INK}; }}
      .card .sub {{ color: {C_INK_SOFT}; font-size: .8rem; }}
      .swatch {{ display:inline-block; width:.7rem; height:.7rem; border-radius:2px; margin-right:.4rem; }}
      .stTabs [data-baseweb="tab-list"] {{ gap: .4rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------------
# Results carried over from the executed notebooks
# These are outputs, not inputs: each one is printed by the notebook named beside it.
# ----------------------------------------------------------------------------------
ENGAGEMENT = pd.DataFrame(                            # notebook 06, descriptive table
    [
        ["gate_30 (all)", 44700, 52.46, 256.72, 17.0, 50.0, 135.0, 493.00, 49854],
        ["gate_30 (outlier removed)", 44699, 51.34, 102.06, 17.0, 50.0, 135.0, 493.00, 2961],
        ["gate_40 (all)", 45489, 51.30, 103.29, 16.0, 52.0, 134.0, 492.12, 2640],
    ],
    columns=["series", "players", "mean", "std", "median", "p75", "p90", "p99", "max"],
)

ENGAGEMENT_TESTS = pd.DataFrame(                      # notebook 06, tests
    [
        ["Welch t-test on means (with the impossible value)", "-1.157 rounds", "0.3759", "Fragile: one row drives it"],
        ["Welch t-test on means (value removed)", "-0.043 rounds", "0.9495", "Nothing left once the outlier goes"],
        ["Mann-Whitney U (rank based)", "P(superiority) 0.4962", "0.0502", "Borderline, effect size negligible"],
        ["Winsorized means (capped at p99 = 493)", "-0.282 rounds", "0.6152", "Robust to the tail, agrees"],
        ["Bootstrap difference in medians", "-1 round (CI -1 to 0)", "-", "Medians move in whole steps"],
    ],
    columns=["Method", "Estimate", "p-value", "Reading"],
)

ROUNDS_BUCKETS = pd.DataFrame(                        # sql/06, descriptive only
    [
        ["0 rounds", 1937, 4.33, 0.83, 2057, 4.52, 0.63],
        ["1-29 rounds", 26107, 58.40, 4.51, 26819, 58.96, 4.18],
        ["30-39 rounds", 3090, 6.91, 15.73, 2786, 6.12, 15.69],
        ["40-99 rounds", 7398, 16.55, 32.90, 7479, 16.44, 29.39],
        ["100-499 rounds", 5740, 12.84, 69.37, 5916, 13.01, 69.19],
        ["500+ rounds", 428, 0.96, 94.86, 432, 0.95, 96.30],
    ],
    columns=["Rounds bucket", "gate_30 players", "gate_30 % of group", "gate_30 D7 %",
             "gate_40 players", "gate_40 % of group", "gate_40 D7 %"],
)

DECILES = pd.DataFrame(                               # notebook 03, SRM by userid band
    [[0, 4474, 4545, 50.39, 0.4547], [1, 4486, 4533, 50.26, 0.6207], [2, 4507, 4512, 50.03, 0.9580],
     [3, 4542, 4477, 49.64, 0.4937], [4, 4391, 4628, 51.31, 0.0126], [5, 4471, 4547, 50.42, 0.4235],
     [6, 4487, 4532, 50.25, 0.6356], [7, 4474, 4545, 50.39, 0.4547], [8, 4450, 4569, 50.66, 0.2102],
     [9, 4418, 4601, 51.01, 0.0540]],
    columns=["userid decile", "gate_30", "gate_40", "gate_40 share %", "SRM p-value"],
)

RETENTION_OVERLAP = pd.DataFrame(                     # sql/07, D1 vs D7 combinations
    [["Did not return on either day", 46437, 51.49], ["Returned on day 7 only", 3599, 3.99],
     ["Returned on day 1 only", 26971, 29.90], ["Returned on both days", 13182, 14.62]],
    columns=["Behaviour", "Players", "Share %"],
)

# Robustness results (notebook 05) - the app recomputes the Bayesian part live, these are the reference values.
BOOTSTRAP = {"D7 retention": (-1.3425, -0.3125, 0.9994), "D1 retention": (-1.2268, 0.0621, 0.9609)}
PERMUTATION = {"shuffles_10k": 0.0016, "mc_error": 0.0004, "exact_2m": 0.00162, "ztest": 0.00155}

# Pitfall results (notebook 07)
PITFALL_FILTER = pd.DataFrame(
    [["gate_30", 19.020, 50.287, 13566], ["gate_40", 18.200, 48.507, 13827]],
    columns=["Version", "D7 % (all players)", "D7 % (only 40+ rounds)", "Players left after filter"],
)
PITFALL_SIM = {"true_effect_pp": -0.02, "filtered_effect_pp": -3.343}
PEEKING = {"once": 0.050, "daily": 0.216, "boundary": 2.632, "calibrated": 0.058}

MDE_REFERENCE = pd.DataFrame(                         # notebook 03
    [["D1 retention", 44.819, 0.928, 2.07], ["D7 retention", 19.020, 0.732, 3.85]],
    columns=["Metric", "Baseline %", "MDE (pp) at 80% power", "MDE relative %"],
)

# Every judgement call in the project, with the alternative that was rejected (notebooks 01-07, the plan and the memo).
DECISIONS = pd.DataFrame(
    [
        ["Primary metric is D7, fixed before analysis",
         "Returning a week after install signals a forming habit, which is closer to long-term value than a first-day visit. One primary metric also limits multiple-testing risk.",
         "Report D1 and D7 as co-primary, then pick whichever looks better afterwards.", "Pre-analysis plan"],
        ["Two-sided tests",
         "A change to a live progression system can just as easily hurt as help, and the data confirmed it hurt. A one-sided test would have had no way to say so.",
         "One-sided test for an improvement only.", "Pre-analysis plan"],
        ["Intention-to-treat: analyse everyone as assigned",
         "Randomisation is what makes the groups comparable. Dropping players after assignment - even players who never reached a gate - breaks that guarantee.",
         "Keep only players who actually reached a gate (40+ rounds).", "Notebooks 02, 04, 07"],
        ["Flag suspicious rows, never delete them",
         "The one impossible rounds value (49,854) stays in the retention analysis and is reported with and without in the engagement analysis, so a reader can see exactly what it changes.",
         "Silently drop the row, or drop all zero-round players.", "Notebook 02"],
        ["Report the borderline SRM instead of discarding the test",
         "p = 0.0086 is flagged at 0.01 but not at the 0.001 threshold most platforms alarm on, the imbalance is spread evenly across userid deciles, and the intended split is undocumented.",
         "Throw the experiment away, or never run the check at all.", "Notebook 03"],
        ["Practical threshold of 0.5 pp, set in advance",
         "On a 19% baseline that is a ~2.6% relative move. Below it, the engineering, QA and player-confusion cost of changing a live gate is not worth paying.",
         "Decide what counts as 'big enough' after seeing the effect size.", "Pre-analysis plan"],
        ["Pooled standard error for the test, unpooled for the interval",
         "The test assumes the null is true, so pooling both groups gives the best noise estimate under that assumption. The interval estimates the real difference and must not assume the rates are equal.",
         "Use one standard error for both and accept the mismatch.", "Notebook 04"],
        ["Holm correction across the two retention metrics",
         "Two tests at 0.05 each carry more than a 5% chance of at least one false positive. Holm controls that while staying more powerful than Bonferroni. D7 survives it (p = 0.0031).",
         "No correction, or the more conservative Bonferroni.", "Notebook 04"],
        ["Confirm with bootstrap, permutation and Bayesian methods",
         "They rest on different assumptions: the bootstrap needs no formula, the permutation test simulates 'no effect' directly, and the Bayesian model answers the decision question. All three agree.",
         "Stop at the z-test because it is significant.", "Notebook 05"],
        ["Rank-based and winsorized tests for rounds played",
         "Rounds are extremely skewed and one impossible value dominates the mean. Medians, ranks and capped means are all robust to that tail, and all three agree.",
         "Compare raw means and report the t-test result as the finding.", "Notebook 06"],
        ["No segment analysis",
         "Fair segments must be defined by attributes measured before assignment. This dataset has none, and rounds played is post-treatment - notebook 07 shows that slicing on it manufactures effects.",
         "Split by rounds played, or by retained versus churned.", "Notebook 07"],
        ["No CUPED variance reduction",
         "CUPED needs pre-experiment behaviour per player to subtract predictable variance. This dataset starts at install, so there is no pre-period to use.",
         "Apply CUPED anyway using in-experiment rounds as the covariate.", "README"],
        ["Analyse once, at the end",
         "Simulated peeking across 2,000 A/A tests raised the false-positive rate from 5.0% to 21.6%. The analysis was run once against rules written in advance.",
         "Watch the dashboard daily and stop at the first significant day.", "Notebook 07"],
        ["Recommend keeping the gate at level 30",
         "D7 fell 0.82 pp with the whole interval below zero, every robustness check agrees, and engagement offers nothing to trade against it. The decision rule for this outcome was written before the analysis.",
         "Ship gate_40 because rounds played were statistically unchanged.", "Decision memo"],
    ],
    columns=["Decision", "Why", "Alternative rejected", "Where"],
)

# ----------------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_counts() -> pd.DataFrame:
    """Read the four numbers per group that every live calculation is built from."""
    return pd.read_csv(SUMMARY_FILE)


def style_axes(ax, xlabel="", ylabel="", title=""):
    """One recessive, consistent look for every chart drawn inside the app."""
    ax.set_facecolor(C_SURFACE)                                  # light chart surface
    ax.figure.patch.set_facecolor(C_SURFACE)                     # matching figure background
    ax.grid(True, color=C_GRID, linewidth=0.8, alpha=0.9)        # grid sits behind the data
    ax.set_axisbelow(True)                                       # never draw grid over marks
    for side in ("top", "right", "left"):                        # drop the box, keep the baseline
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(C_GRID)                        # recessive axis line
    ax.tick_params(colors=C_INK_SOFT, labelsize=9)               # secondary ink for ticks
    if xlabel:
        ax.set_xlabel(xlabel, color=C_INK_SOFT, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=C_INK_SOFT, fontsize=10)
    if title:
        ax.set_title(title, color=C_INK, fontsize=12, fontweight="bold", loc="left")
    return ax


def render(fig):
    """Draw a matplotlib figure and release it, because Streamlit reruns the script on every click."""
    st.pyplot(fig)
    plt.close(fig)


def ab_test(x_a, n_a, x_b, n_b, alpha=0.05):
    """Two-proportion z-test plus a Wald interval. A is control, B is treatment."""
    rate_a = x_a / n_a                                           # control rate
    rate_b = x_b / n_b                                           # treatment rate
    diff = rate_b - rate_a                                       # absolute difference
    pooled = (x_a + x_b) / (n_a + n_b)                           # pooled rate, assuming no difference
    se_pooled = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))          # standard error for the test
    z_stat = diff / se_pooled if se_pooled > 0 else 0.0                       # z-statistic
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))                           # two-sided p-value
    se_unpooled = np.sqrt(rate_a * (1 - rate_a) / n_a + rate_b * (1 - rate_b) / n_b)   # standard error for the interval
    z_crit = stats.norm.ppf(1 - alpha / 2)                                    # critical value
    return {
        "rate_a": rate_a, "rate_b": rate_b, "diff": diff,
        "relative": diff / rate_a if rate_a > 0 else float("nan"),
        "z": z_stat, "p": p_value,
        "ci_low": diff - z_crit * se_unpooled, "ci_high": diff + z_crit * se_unpooled,
        "se_pooled": se_pooled, "se_unpooled": se_unpooled, "pooled": pooled,
        "confidence": int(round((1 - alpha) * 100)),
    }


@st.cache_data(show_spinner=False)
def bayes_compare(x_a, n_a, x_b, n_b, prior_a=1.0, prior_b=1.0, draws=100000, seed=0):
    """Beta-Binomial posterior draws for both groups, then the quantities a team decides on."""
    rng = np.random.default_rng(seed)                                          # fixed seed: numbers do not jump on rerun
    post_a = rng.beta(prior_a + x_a, prior_b + n_a - x_a, size=draws)          # posterior for the control rate
    post_b = rng.beta(prior_a + x_b, prior_b + n_b - x_b, size=draws)          # posterior for the treatment rate
    d = post_b - post_a                                                        # posterior for the difference
    return {
        "post_a": post_a, "post_b": post_b,
        "prob_b_better": float(np.mean(d > 0)),                                # chance the treatment is truly better
        "loss_b": float(np.mean(np.maximum(-d, 0))),                           # expected loss if we ship the treatment
        "loss_a": float(np.mean(np.maximum(d, 0))),                            # expected loss if we keep the control
        "cred_low": float(np.percentile(d, 2.5)), "cred_high": float(np.percentile(d, 97.5)),
    }


@st.cache_data(show_spinner=False)
def permutation_p(x_a, n_a, x_b, n_b, shuffles=200000, seed=2024):
    """Exact-style permutation p-value: shuffling labels only moves retained players between groups."""
    rng = np.random.default_rng(seed)                                          # fixed seed
    total, retained = n_a + n_b, x_a + x_b                                     # pooled totals
    observed = abs(x_b / n_b - x_a / n_a)                                      # the difference we actually saw
    in_b = rng.hypergeometric(retained, total - retained, n_b, size=shuffles)  # retained players landing in fake B
    diffs = in_b / n_b - (retained - in_b) / n_a                               # difference under the null
    return float(np.mean(np.abs(diffs) >= observed - 1e-12)), diffs            # share at least as extreme


@st.cache_data(show_spinner=False)
def peeking_simulation(n_experiments, n_days, players_per_day, true_rate, seed):
    """A/A tests where both groups are identical, so every 'significant' result is a false positive."""
    rng = np.random.default_rng(seed)                                          # fixed seed
    cum_n = players_per_day * np.arange(1, n_days + 1)                         # cumulative players per group per day
    a = np.cumsum(rng.binomial(players_per_day, true_rate, size=(n_experiments, n_days)), axis=1)   # group A
    b = np.cumsum(rng.binomial(players_per_day, true_rate, size=(n_experiments, n_days)), axis=1)   # group B
    pooled = (a + b) / (2 * cum_n)                                             # pooled rate on each day
    se = np.sqrt(pooled * (1 - pooled) * (2 / cum_n))                          # standard error on each day
    z = (b / cum_n - a / cum_n) / se                                           # z on each day, all experiments at once
    return np.abs(z).max(axis=1), np.abs(z[:, -1])                             # biggest |z| ever seen, and the final one


def mde_pp(baseline, n_per_group, alpha=0.05, power=0.80):
    """Smallest absolute difference this sample size can detect, in percentage points."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)                                    # two-sided critical value
    z_power = stats.norm.ppf(power)                                            # value for the target power
    se = np.sqrt(baseline * (1 - baseline) * (2 / n_per_group))                # standard error of the difference
    return 100 * (z_alpha + z_power) * se


def sample_size_per_group(baseline, mde_absolute, alpha=0.05, power=0.80):
    """Players per group needed to detect a drop of mde_absolute from baseline."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)                                    # two-sided critical value
    z_power = stats.norm.ppf(power)                                            # value for the target power
    p1, p2 = baseline, baseline - mde_absolute                                 # the two rates we want to tell apart
    return ((z_alpha + z_power) ** 2) * (p1 * (1 - p1) + p2 * (1 - p2)) / (p1 - p2) ** 2


def cards(items):
    """A row of stat tiles. items = list of (label, value, sub-line)."""
    cols = st.columns(len(items))
    for col, (label, value, sub) in zip(cols, items):
        col.markdown(
            f'<div class="card"><div class="lab">{label}</div>'
            f'<div class="val">{value}</div><div class="sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )


def figure(name, caption):
    """Show one of the PNG charts the notebooks produced."""
    path = FIG_DIR / name
    if path.exists():
        st.image(str(path), caption=caption, width="stretch")
    else:
        st.info(f"Chart `{name}` is not in the repository. Run the notebooks to regenerate `reports/figures/`.")


def ci_chart(rows, threshold_pp, confidence):
    """Point estimate with its interval, against zero and the practical threshold."""
    fig, ax = plt.subplots(figsize=(9, 1.1 + 0.9 * len(rows)))
    y = np.arange(len(rows))
    lows = [r["diff_pp"] - r["ci_low_pp"] for r in rows]
    highs = [r["ci_high_pp"] - r["diff_pp"] for r in rows]
    colors = [C_TREAT if r["primary"] else C_CONTROL for r in rows]
    for i, r in enumerate(rows):                                   # one interval per metric, drawn in its own colour
        ax.errorbar(r["diff_pp"], i, xerr=[[lows[i]], [highs[i]]], fmt="o", markersize=9,
                    capsize=7, linewidth=2, color=colors[i])
        ax.annotate(f'{r["diff_pp"]:+.2f} pp', (r["diff_pp"], i), textcoords="offset points",
                    xytext=(0, 14), ha="center", color=C_INK, fontsize=10, fontweight="bold")
    ax.axvline(0, color=C_INK, linewidth=1.2)                      # no difference
    ax.axvline(-threshold_pp, color=C_BAD, linestyle="--", linewidth=1)   # practical threshold, negative side
    ax.axvline(threshold_pp, color=C_BAD, linestyle="--", linewidth=1)    # practical threshold, positive side
    ax.set_yticks(y)
    ax.set_yticklabels([r["metric"] for r in rows], color=C_INK, fontsize=10)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    style_axes(ax, xlabel=f"gate_40 minus gate_30 (percentage points), {confidence}% CI")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def srm_banner(p_value):
    """The three-way sample ratio mismatch verdict used across the app."""
    if p_value < 0.001:
        st.error(f"**Sample ratio mismatch detected** (p = {p_value:.5f}). Investigate assignment and logging before trusting any result.")
    elif p_value < 0.01:
        st.warning(f"**Borderline sample ratio mismatch** (p = {p_value:.5f}). Report it, investigate it, but it is not an automatic failure.")
    else:
        st.success(f"**No sample ratio mismatch detected** (p = {p_value:.4f}).")


# ----------------------------------------------------------------------------------
# Shared state
# ----------------------------------------------------------------------------------
counts = load_counts()                                             # the committed summary table
CTRL = counts[counts["version"] == "gate_30"].iloc[0]              # control row
TRT = counts[counts["version"] == "gate_40"].iloc[0]               # treatment row
N_A, N_B = int(CTRL["players"]), int(TRT["players"])               # players per group
X_A7, X_B7 = int(CTRL["d7_retained"]), int(TRT["d7_retained"])     # D7 retained per group
X_A1, X_B1 = int(CTRL["d1_retained"]), int(TRT["d1_retained"])     # D1 retained per group
TOTAL_PLAYERS = N_A + N_B                                          # 90,189

D7 = ab_test(X_A7, N_A, X_B7, N_B)                                 # headline result
D1 = ab_test(X_A1, N_A, X_B1, N_B)                                 # secondary result
SRM_P = float(stats.chisquare([N_A, N_B], f_exp=[TOTAL_PLAYERS / 2, TOTAL_PLAYERS / 2]).pvalue)   # validity check

# ----------------------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------------------
PAGES = [
    "1 · Verdict",
    "2 · The experiment",
    "3 · Data quality",
    "4 · Validity & power",
    "5 · Retention results",
    "6 · Robustness checks",
    "7 · Engagement",
    "8 · Pitfalls proven",
    "9 · Decision log",
    "10 · Analyze your own test",
    "11 · Plan a test",
    "12 · Method & reproducibility",
]

with st.sidebar:
    st.markdown("### 🍪 Cookie Cats A/B test")
    st.caption("Should the first progression gate move from level 30 to level 40?")
    page = st.radio("Section", PAGES, label_visibility="collapsed")
    st.divider()
    st.markdown(
        f'<span class="swatch" style="background:{C_CONTROL}"></span> gate_30 · control<br>'
        f'<span class="swatch" style="background:{C_TREAT}"></span> gate_40 · treatment',
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption(
        f"**{TOTAL_PLAYERS:,} players** · randomised at install\n\n"
        "Every number on every page is either recomputed live from the group counts "
        "or taken from the executed notebooks in this repository."
    )

# ==================================================================================
# 1 - Verdict
# ==================================================================================
if page == PAGES[0]:
    st.title("Verdict: keep the first gate at level 30")
    st.markdown(
        f"""
        <div class="hero">
          <h2>Moving the gate to level 40 lowered 7-day retention</h2>
          <p>Across {TOTAL_PLAYERS:,} randomly assigned players, D7 retention fell from
          <b>{100 * D7['rate_a']:.2f}%</b> to <b>{100 * D7['rate_b']:.2f}%</b> - a drop of
          <b>{100 * D7['diff']:.2f} percentage points</b> ({100 * D7['relative']:.1f}% relative),
          95% CI {100 * D7['ci_low']:.2f} to {100 * D7['ci_high']:.2f} pp, p = {D7['p']:.4f}.
          Every robustness check agrees, engagement offers nothing to trade against it, and the decision
          rule for this outcome was written before the analysis ran.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards([
        ("D7 retention · gate_30", f"{100 * D7['rate_a']:.2f}%", f"{X_A7:,} of {N_A:,} players"),
        ("D7 retention · gate_40", f"{100 * D7['rate_b']:.2f}%", f"{X_B7:,} of {N_B:,} players"),
        ("Absolute difference", f"{100 * D7['diff']:+.2f} pp", f"{100 * D7['relative']:+.1f}% relative"),
        ("Two-sided p-value", f"{D7['p']:.4f}", f"z = {D7['z']:.3f}"),
    ])
    st.write("")
    cards([
        ("Players affected", "≈82 per 10,000", "fewer day-7 returners under gate_40"),
        ("P(gate_40 truly better)", "≈0.1%", "Bayesian Beta-Binomial, notebook 05"),
        ("Expected loss if shipped", "0.82 pp", "versus ≈0.00 pp for keeping gate_30"),
        ("Validity flag", "Borderline SRM", f"p = {SRM_P:.4f} against an assumed 50/50 split"),
    ])

    st.divider()
    left, right = st.columns([3, 2])
    with left:
        st.subheader("The result in one chart")
        threshold = st.slider("Practical significance threshold (pp)", 0.0, 2.0, 0.5, 0.1,
                              help="The smallest change worth acting on. The pre-analysis plan fixed this at 0.5 pp.")
        rows = [
            {"metric": "D7 retention (primary)", "diff_pp": 100 * D7["diff"], "ci_low_pp": 100 * D7["ci_low"],
             "ci_high_pp": 100 * D7["ci_high"], "primary": True},
            {"metric": "D1 retention (secondary)", "diff_pp": 100 * D1["diff"], "ci_low_pp": 100 * D1["ci_low"],
             "ci_high_pp": 100 * D1["ci_high"], "primary": False},
        ]
        render(ci_chart(rows, threshold, D7["confidence"]))
        st.caption(
            "Dots are the observed differences; bars are 95% confidence intervals. The black line is "
            "'no difference'; the dashed red lines are the practical threshold you set above."
        )
    with right:
        st.subheader("How to read it")
        st.markdown(
            f"""
- **The D7 interval sits entirely below zero.** The data is compatible with a true drop between
  {abs(100 * D7['ci_high']):.2f} and {abs(100 * D7['ci_low']):.2f} pp - and not with zero.
- **The point estimate clears the {threshold:.1f} pp threshold, the interval does not fully.**
  Say it exactly that way: the effect is clearly negative and most plausibly meaningful, though the
  true drop could be somewhat smaller than the threshold.
- **D1 crosses zero.** Not significant (p = {D1['p']:.4f}), same direction, and with a detection floor
  of 0.93 pp the test could easily have missed a real 0.5 pp D1 effect. "Not significant" is not "no effect".
            """
        )
        st.info("The decision rule was fixed in advance: if the D7 interval sits entirely below zero, keep the gate at level 30.")

    st.divider()
    st.subheader("What this costs the business")
    st.markdown(
        f"""
        Out of every **10,000 new players, about {abs(100 * D7['diff']) * 100:.0f} fewer come back on day 7**
        under gate_40. Week-one retention is the top of every later funnel - sessions, ad impressions and
        purchases all scale off the players still present on day 7 - so a {abs(100 * D7['relative']):.1f}% relative
        loss compounds through the rest of the player lifetime. There is no upside to weigh against it:
        rounds played are statistically indistinguishable between the two versions (page 7).
        """
    )

# ==================================================================================
# 2 - The experiment
# ==================================================================================
elif page == PAGES[1]:
    st.title("The experiment")
    st.markdown(
        """
        <div class="hero">
          <h2>One change, randomised at install</h2>
          <p>Cookie Cats is a match-three mobile puzzle game. As players progress they hit <b>gates</b>:
          points where they must either wait or make an in-app purchase to continue. New players were
          randomly assigned to a first gate at level 30 (the current version) or level 40.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a, b = st.columns(2)
    with a:
        st.subheader("Design")
        st.markdown(
            f"""
| Element | Choice |
|---|---|
| Unit of randomisation | The player, at install |
| Control | `gate_30` - first gate at level 30 ({N_A:,} players) |
| Treatment | `gate_40` - first gate at level 40 ({N_B:,} players) |
| Primary metric | D7 retention (`retention_7`) |
| Secondary metric | D1 retention (`retention_1`) |
| Understanding metric | Game rounds (`sum_gamerounds`) - never a ship criterion |
| Population | Intention-to-treat: every randomised player |
| Significance level | alpha = 0.05, two-sided |
| Target power | 80% |
| Practical threshold | 0.5 pp absolute on D7 |
            """
        )
    with b:
        st.subheader("Why a gate is worth testing")
        st.markdown(
            """
A gate is a deliberate stop. It paces progression, protects the difficulty curve, and creates the
moment where a player either waits, invites friends, or pays. Moving it later sounds player-friendly -
ten more levels before the first forced break - but it also removes an early, natural stopping point
and delays the first monetisation prompt.

The test answers only the first half of that: **does the later gate keep more players?** It carries no
revenue data, so it cannot answer the monetisation half. That gap is stated as a limitation rather than
papered over.
            """
        )
        st.warning(
            "**Intention-to-treat matters here.** Many players never reach either gate. They stay in the "
            "analysis anyway: dropping them would compare survivors to survivors, and page 8 shows what that does."
        )

    st.divider()
    st.subheader("The data")
    st.markdown(
        """
| Column | Type | Meaning |
|---|---|---|
| `userid` | integer | Unique anonymised player ID |
| `version` | text | `gate_30` (control) or `gate_40` (treatment) |
| `sum_gamerounds` | integer | Rounds played after installing |
| `retention_1` | boolean | Came back and played 1 day after installing |
| `retention_7` | boolean | Came back and played 7 days after installing |
        """
    )
    st.caption("90,189 rows, one per player. No revenue, no install date, no player attributes.")

    st.subheader("D1 and D7 are related but separate behaviours")
    left, right = st.columns([2, 3])
    with left:
        st.dataframe(RETENTION_OVERLAP, hide_index=True, width="stretch")
    with right:
        fig, ax = plt.subplots(figsize=(7, 3.2))
        labels = RETENTION_OVERLAP["Behaviour"]
        vals = RETENTION_OVERLAP["Share %"]
        bars = ax.barh(labels, vals, color=[C_GRID, C_TREAT, C_CONTROL, C_GOOD], height=0.62)
        for bar, v in zip(bars, vals):                                  # direct labels: four bars, so label them all
            ax.annotate(f"{v:.2f}%", (v, bar.get_y() + bar.get_height() / 2),
                        xytext=(6, 0), textcoords="offset points", va="center",
                        color=C_INK_SOFT, fontsize=9)
        ax.set_xlim(0, 60)
        style_axes(ax, xlabel="Share of all players (%)")
        ax.grid(axis="y", visible=False)
        fig.tight_layout()
        render(fig)
    st.markdown(
        "**3,599 players (3.99%) skipped day 1 and still returned on day 7.** That is why D7 is not a "
        "subset of D1, and why a D1 result cannot stand in for the primary metric."
    )

# ==================================================================================
# 3 - Data quality
# ==================================================================================
elif page == PAGES[2]:
    st.title("Data quality: flag, never delete")
    st.markdown(
        """
        <div class="hero">
          <h2>What the data looks like before anything is tested</h2>
          <p>Structurally the file is clean: 90,189 rows, 90,189 distinct players, zero duplicates and
          zero nulls. The interesting problems are in the values, not the structure - and none of them
          is fixed by deleting a row.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards([
        ("Rows / distinct players", "90,189 / 90,189", "no duplicates, no nulls"),
        ("Zero-round players", "3,994", "installed, never played a round"),
        ("Physically impossible rows", "1", "49,854 rounds by one player"),
        ("Retained with zero rounds", "111", "56 gate_30 · 55 gate_40"),
    ])

    st.divider()
    st.subheader("The 49,854-round player")
    a, b = st.columns([3, 2])
    with a:
        st.markdown(
            """
The largest value in the dataset is **49,854 rounds**. The second largest, in the same group, is
**2,961** - about 17 times smaller.

Spread over 14 days (the longest measurement window any source claims for this column) that is about
**3,561 rounds per day**. Now put a floor under how long a round takes: at 30 seconds per round, with
no sleep, no breaks and no app switching, 24 hours allows at most **2,880 rounds per day**.

The value is not merely extreme, it is **impossible**. It is a logging error or a bot.
            """
        )
        st.success(
            "**Decision: flag it, do not delete it.** It stays in the retention analysis (intention-to-treat) "
            "and the engagement analysis is reported with and without it, so the reader can see exactly what "
            "it changes. Page 7 shows it changes the mean and nothing else."
        )
    with b:
        fig, ax = plt.subplots(figsize=(5.4, 3.4))
        names = ["Impossible\nrow", "2nd highest\n(gate_30)", "Highest\n(gate_40)", "Median\nplayer"]
        vals = [49854, 2961, 2640, 17]
        colors = [C_BAD, C_CONTROL, C_TREAT, C_GRID]
        bars = ax.bar(names, vals, color=colors, width=0.62)
        ax.set_yscale("log")
        for bar, v in zip(bars, vals):                                  # four bars: direct labels beat a legend
            ax.annotate(f"{v:,}", (bar.get_x() + bar.get_width() / 2, v),
                        xytext=(0, 5), textcoords="offset points", ha="center",
                        color=C_INK_SOFT, fontsize=9)
        style_axes(ax, ylabel="Rounds played (log scale)")
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        render(fig)

    st.divider()
    st.subheader("111 players are marked as retained with zero rounds")
    st.markdown(
        """
The dataset describes retention as *came back and played*, yet 111 players have zero rounds and a
retention flag set. That is an internal contradiction in the logging, not something the analysis can
resolve. Two things make it tolerable:

- It is **tiny**: 111 of 90,189 players, about 0.12%.
- It is **balanced**: 56 in gate_30 and 55 in gate_40, so it cannot plausibly tilt a comparison between them.

It is reported as a data-quality issue and listed in the memo as something for the team to fix upstream.
        """
    )

    st.divider()
    st.subheader("Rounds played are extremely skewed")
    c1, c2 = st.columns(2)
    with c1:
        figure("01_rounds_distribution_log.png", "Distribution of rounds per player, log scale (+1 so zeros are visible)")
        st.caption(
            "A log scale is not decoration here: values run from 0 to 50,000, so on a linear axis the "
            "thousands of casual players collapse into a single bar."
        )
    with c2:
        figure("02_rounds_ecdf.png", "Cumulative share of players by rounds played")
        st.caption(
            "The two curves sit almost on top of each other. Whatever the gate did, it did not reshape "
            "how much people play."
        )
    st.markdown(
        "**The mean is about 52 while the median is about 17.** When the mean is three times the median, "
        "the mean is describing the tail, not a typical player - which is why page 7 leans on medians, "
        "ranks and capped means instead."
    )

# ==================================================================================
# 4 - Validity and power
# ==================================================================================
elif page == PAGES[3]:
    st.title("Validity and power: can this experiment be trusted, and what could it see?")
    st.markdown(
        """
        <div class="hero">
          <h2>Both questions get answered before any outcome is looked at</h2>
          <p>A sample ratio mismatch can mean assignment or logging is broken, which would bias every
          number that follows. The minimum detectable effect says what the test was capable of finding
          in the first place - it is what turns "not significant" into a precise statement.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Sample ratio mismatch (SRM)")
    a, b = st.columns([2, 3])
    with a:
        share_b = st.slider("Intended share for gate_40", 0.40, 0.60, 0.50, 0.01,
                            help="The dataset does not document the intended split. 50/50 is an assumption.")
        expected = [TOTAL_PLAYERS * (1 - share_b), TOTAL_PLAYERS * share_b]
        chi2 = float(stats.chisquare([N_A, N_B], f_exp=expected).statistic)
        p_now = float(stats.chisquare([N_A, N_B], f_exp=expected).pvalue)
        st.metric("Chi-square statistic", f"{chi2:.3f}")
        st.metric("SRM p-value", f"{p_now:.5f}")
        st.caption(f"Observed: gate_30 {N_A:,} · gate_40 {N_B:,} (a gap of {N_B - N_A:,} players)")
    with b:
        srm_banner(p_now)
        st.markdown(
            f"""
At the assumed 50/50 design the imbalance gives **p = {SRM_P:.5f}**:

| Threshold | Flagged? | Who uses it |
|---|---|---|
| 0.05 | Yes | Rarely - far too many false alarms across many experiments |
| 0.01 | Yes | A cautious investigate-it line |
| 0.001 | **No** | The alarm threshold most experimentation platforms actually fire on |

Slide the intended share above to see how much of this conclusion rests on the 50/50 assumption:
a design of roughly 49.6/50.4 would make the observed counts entirely unremarkable.
            """
        )

    with st.expander("Diagnostic: is the imbalance concentrated in one range of user IDs?"):
        st.markdown(
            "If a specific ID range were broken, its band would show a large imbalance. Instead the small "
            "tilt toward gate_40 is spread evenly: gate_40 holds more than half in **9 of 10 bands**, and only "
            "one band dips below p = 0.05. This is exploratory - nothing in the data confirms that user IDs "
            "follow install order."
        )
        st.dataframe(DECILES, hide_index=True, width="stretch")
        fig, ax = plt.subplots(figsize=(9, 2.8))
        ax.bar(DECILES["userid decile"], DECILES["gate_40 share %"] - 50, color=C_TREAT, width=0.6)
        ax.axhline(0, color=C_INK, linewidth=1.2)
        ax.set_xticks(DECILES["userid decile"])
        style_axes(ax, xlabel="userid decile", ylabel="gate_40 share minus 50 (pp)")
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        render(fig)

    st.success(
        "**Decision: report it, investigate it, do not discard the test.** Borderline under the standard "
        "alarm threshold, evenly spread, and measured against an undocumented intended split. Silently "
        "ignoring it and throwing the test away are both wrong."
    )

    st.divider()
    st.subheader("What could this test actually detect?")
    a, b = st.columns([2, 3])
    with a:
        baseline_pct = st.slider("Baseline D7 retention (%)", 5.0, 40.0, float(100 * D7["rate_a"]), 0.1)
        n_slider = st.slider("Players per group", 5000, 200000, int((N_A + N_B) / 2), 5000, format="%d")
        power_choice = st.select_slider("Target power", [0.70, 0.80, 0.90], value=0.80)
        base = baseline_pct / 100
        this_mde = mde_pp(base, n_slider, 0.05, power_choice)
        st.metric("Minimum detectable effect", f"{this_mde:.3f} pp", f"{this_mde / baseline_pct * 100:.2f}% relative")
        needed = sample_size_per_group(base, 0.005, 0.05, power_choice)
        st.metric("Players needed for a 0.5 pp effect", f"{int(np.ceil(needed)):,}")
    with b:
        fig, ax = plt.subplots(figsize=(8, 4))
        ns = np.linspace(5000, 200000, 200)
        ax.plot(ns, [mde_pp(base, n, 0.05, power_choice) for n in ns], color=C_CONTROL, linewidth=2)
        ax.axvline(n_slider, color=C_TREAT, linestyle="--", linewidth=1.5)
        ax.axhline(this_mde, color=C_TREAT, linestyle=":", linewidth=1.5)
        ax.annotate(f"{this_mde:.2f} pp at {n_slider:,}/group", (n_slider, this_mde),
                    xytext=(10, 14), textcoords="offset points", color=C_INK, fontsize=10, fontweight="bold")
        style_axes(ax, xlabel="Players per group", ylabel="Detectable difference (pp)",
                   title="Bigger samples see smaller effects")
        fig.tight_layout()
        render(fig)

    st.dataframe(MDE_REFERENCE, hide_index=True, width="stretch")
    st.markdown(
        """
**The consequence, in one sentence:** with about 45,000 players per group this test had an 80% chance
of catching a true D7 change of **0.73 pp or larger**, so the 0.5 pp change the plan calls meaningful
could easily have slipped past it. Detecting 0.5 pp reliably needs about **95,700 players per group** -
more than twice what was run.
        """
    )
    figure("04_power_curve_d7.png", "Power curve at the actual sample sizes: power rises with the true effect, crossing 80% at the MDE")
    st.info(
        "Power analysis belongs to planning and to reading a null result. Computing 'observed power' from "
        "the p-value you already have adds no information - it is just the p-value again in other clothes."
    )

# ==================================================================================
# 5 - Retention results
# ==================================================================================
elif page == PAGES[4]:
    st.title("Retention results")
    st.markdown(
        """
        <div class="hero">
          <h2>Calculated by hand first, then checked against two libraries</h2>
          <p>Every number below is recomputed live from the four counts per group. The notebooks derive the
          same numbers from the formula, then confirm them with statsmodels and a chi-square test - a result
          that only one method produces is a result nobody has checked.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctrl_row, set_row = st.columns([3, 2])
    with ctrl_row:
        metric_choice = st.segmented_control("Metric", ["D7 retention (primary)", "D1 retention (secondary)"],
                                             default="D7 retention (primary)")
    with set_row:
        alpha = st.select_slider("Significance level (alpha)", [0.01, 0.05, 0.10], value=0.05)

    is_d7 = metric_choice is None or metric_choice.startswith("D7")
    x_a, x_b = (X_A7, X_B7) if is_d7 else (X_A1, X_B1)
    res = ab_test(x_a, N_A, x_b, N_B, alpha)

    cards([
        ("gate_30 (control)", f"{100 * res['rate_a']:.2f}%", f"{x_a:,} of {N_A:,}"),
        ("gate_40 (treatment)", f"{100 * res['rate_b']:.2f}%", f"{x_b:,} of {N_B:,}"),
        ("Difference", f"{100 * res['diff']:+.2f} pp", f"{100 * res['relative']:+.2f}% relative"),
        (f"{res['confidence']}% confidence interval", f"{100 * res['ci_low']:.2f} to {100 * res['ci_high']:.2f} pp",
         "treatment minus control"),
    ])
    st.write("")
    cards([
        ("z-statistic", f"{res['z']:.4f}", "difference / pooled standard error"),
        ("p-value (two-sided)", f"{res['p']:.5f}", "chance of a gap this large if nothing changed"),
        ("Chi-square (2x2)", f"{res['z'] ** 2:.4f}", "equals z squared, exactly"),
        ("Significant at alpha", "Yes" if res["p"] < alpha else "No", f"alpha = {alpha}"),
    ])

    st.divider()
    left, right = st.columns([3, 2])
    with left:
        threshold = st.slider("Practical significance threshold (pp)", 0.0, 2.0, 0.5, 0.1)
        rows = [
            {"metric": "D7 retention (primary)", "diff_pp": 100 * D7["diff"], "ci_low_pp": 100 * D7["ci_low"],
             "ci_high_pp": 100 * D7["ci_high"], "primary": True},
            {"metric": "D1 retention (secondary)", "diff_pp": 100 * D1["diff"], "ci_low_pp": 100 * D1["ci_low"],
             "ci_high_pp": 100 * D1["ci_high"], "primary": False},
        ]
        render(ci_chart(rows, threshold, res["confidence"]))
    with right:
        st.subheader("Verdict")
        if res["p"] < alpha and res["diff"] < 0:
            st.error(f"**gate_40 performs significantly worse** on {metric_choice or 'D7 retention'}: "
                     f"{100 * res['diff']:+.2f} pp ({100 * res['relative']:+.1f}% relative).")
        elif res["p"] < alpha:
            st.success(f"**gate_40 performs significantly better**: {100 * res['diff']:+.2f} pp.")
        else:
            st.warning(f"**No statistically significant difference** at alpha = {alpha}. The interval still "
                       f"admits anything from {100 * res['ci_low']:.2f} to {100 * res['ci_high']:.2f} pp.")
        st.markdown(
            f"""
- Interval entirely below zero? **{"Yes" if res['ci_high'] < 0 else "No"}**
- Point estimate past the {threshold:.1f} pp threshold? **{"Yes" if abs(100 * res['diff']) >= threshold else "No"}**
- Whole interval past it? **{"Yes" if res['ci_high'] < 0 and abs(100 * res['ci_high']) >= threshold else "No"}**
            """
        )
        st.caption("The pre-analysis plan ties the ship decision to the first of these, and reports the other two.")

    with st.expander("Show the arithmetic, step by step"):
        st.markdown(
            f"""
**1. The two rates**
`p_control = {x_a:,} / {N_A:,} = {res['rate_a']:.6f}` and `p_treatment = {x_b:,} / {N_B:,} = {res['rate_b']:.6f}`,
so the difference is `{res['diff']:.6f}` = **{100 * res['diff']:.3f} pp**.

**2. Standard error for the test (pooled).** The test asks "what if the gate changed nothing?", so under
that assumption both groups share one rate:
`p_pooled = ({x_a:,} + {x_b:,}) / ({N_A:,} + {N_B:,}) = {res['pooled']:.6f}`, giving
`SE_pooled = sqrt(p(1-p)(1/n_a + 1/n_b)) = {res['se_pooled']:.6f}`.

**3. The test statistic.** `z = {res['diff']:.6f} / {res['se_pooled']:.6f} = {res['z']:.4f}`, and a
two-sided p-value of **{res['p']:.5f}**.

**4. Standard error for the interval (unpooled).** The interval estimates the real difference, so it must
not assume the rates are equal: `SE_unpooled = {res['se_unpooled']:.6f}`, and
`{100 * res['diff']:.3f} ± {stats.norm.ppf(1 - alpha / 2):.3f} × {100 * res['se_unpooled']:.3f}`
gives **{100 * res['ci_low']:.3f} to {100 * res['ci_high']:.3f} pp**.

That split - pooled for the test, unpooled for the interval - is the single most common thing to get
wrong in a two-proportion comparison.
            """
        )

    st.divider()
    st.subheader("Two metrics were tested, so the p-values are corrected")
    p_sorted = sorted([("D7 retention", D7["p"]), ("D1 retention", D1["p"])], key=lambda t: t[1])
    holm = []
    running = 0.0
    for rank, (name, p) in enumerate(p_sorted):
        adj = min(1.0, max(running, p * (len(p_sorted) - rank)))          # Holm: multiply by remaining tests, keep monotone
        running = adj
        holm.append({"Metric": name, "Raw p": round(p, 5), "Holm-adjusted p": round(adj, 5),
                     "Significant at 0.05": "Yes" if adj < 0.05 else "No"})
    st.dataframe(pd.DataFrame(holm), hide_index=True, width="stretch")
    st.markdown(
        "Holm sorts the p-values, multiplies the smallest by the number of tests, the next by one fewer, and "
        "keeps the sequence monotone. It controls the chance of *any* false positive across the family while "
        "staying more powerful than Bonferroni. **D7 survives it.**"
    )
    figure("03_retention_rates.png", "Retention rates by version with 95% intervals (notebook 02)")

    st.download_button(
        "Download these results as CSV",
        pd.DataFrame([
            {"metric": "D7 retention", "control_pct": 100 * D7["rate_a"], "treatment_pct": 100 * D7["rate_b"],
             "diff_pp": 100 * D7["diff"], "ci_low_pp": 100 * D7["ci_low"], "ci_high_pp": 100 * D7["ci_high"],
             "z": D7["z"], "p": D7["p"]},
            {"metric": "D1 retention", "control_pct": 100 * D1["rate_a"], "treatment_pct": 100 * D1["rate_b"],
             "diff_pp": 100 * D1["diff"], "ci_low_pp": 100 * D1["ci_low"], "ci_high_pp": 100 * D1["ci_high"],
             "z": D1["z"], "p": D1["p"]},
        ]).to_csv(index=False),
        file_name="retention_test_results.csv", mime="text/csv",
    )

# ==================================================================================
# 6 - Robustness
# ==================================================================================
elif page == PAGES[5]:
    st.title("Robustness: three methods, three sets of assumptions")
    st.markdown(
        """
        <div class="hero">
          <h2>A result that survives only one method has not been tested</h2>
          <p>The bootstrap uses no formula. The permutation test builds the null world directly by shuffling
          labels. The Bayesian model answers the question a product team actually asks. If all three land on
          the z-test answer, the conclusion is not an artefact of one set of assumptions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.tabs(["Bootstrap", "Permutation test", "Bayesian"])

    with t1:
        st.subheader("Resample the players, 10,000 times")
        st.markdown(
            """
Each resample draws players from a group **with replacement**, so some appear twice and others not at
all. It imitates re-running the same experiment on a different set of similar players. No normal
approximation, no formula - just the spread of what the estimate does.
            """
        )
        boot = pd.DataFrame([
            {"Metric": m, "Bootstrap 95% CI (pp)": f"{lo:.3f} to {hi:.3f}",
             "Formula 95% CI (pp)": (f"{100 * D7['ci_low']:.3f} to {100 * D7['ci_high']:.3f}" if m == "D7 retention"
                                     else f"{100 * D1['ci_low']:.3f} to {100 * D1['ci_high']:.3f}"),
             "Resamples where gate_30 won": f"{share:.4f}"}
            for m, (lo, hi, share) in BOOTSTRAP.items()
        ])
        st.dataframe(boot, hide_index=True, width="stretch")
        st.success(
            "The bootstrap interval lands on the formula interval to within about a hundredth of a "
            "percentage point. With samples this large the normal approximation is excellent - now demonstrated "
            "rather than assumed."
        )
        figure("06_bootstrap_d7.png", "Bootstrap distributions of D7 retention per group, and of the difference")

    with t2:
        st.subheader("Shuffle the labels and see how rare the real gap is")
        st.markdown(
            """
Shuffling group labels creates worlds where the gate does nothing by construction. Shuffling only moves
retained players between groups, and the number landing in the fake treatment group follows a
**hypergeometric** distribution - so millions of shuffles can be drawn directly instead of reordering
90,189 values over and over.
            """
        )
        shuffles = st.select_slider("Shuffles to draw", [50000, 200000, 500000, 1000000, 2000000], value=200000)
        p_perm, perm_diffs = permutation_p(X_A7, N_A, X_B7, N_B, shuffles)
        mc_err = np.sqrt(max(p_perm, 1e-9) * (1 - p_perm) / shuffles)
        c1, c2, c3 = st.columns(3)
        c1.metric("Permutation p-value", f"{p_perm:.5f}", f"± {mc_err:.5f} simulation error")
        c2.metric("z-test p-value", f"{D7['p']:.5f}", "for comparison")
        c3.metric("Notebook reference", f"{PERMUTATION['exact_2m']:.5f}", "2,000,000 shuffles")
        fig, ax = plt.subplots(figsize=(9, 3.6))
        ax.hist(100 * perm_diffs, bins=80, color=C_GRID, edgecolor="none")
        ax.axvline(100 * D7["diff"], color=C_TREAT, linewidth=2.5)
        ax.annotate("observed difference", (100 * D7["diff"], ax.get_ylim()[1] * 0.75),
                    xytext=(12, 0), textcoords="offset points", color=C_INK, fontsize=10, fontweight="bold")
        style_axes(ax, xlabel="Difference when the label means nothing (pp)", ylabel="Shuffles",
                   title="The null world, and where the real result falls in it")
        fig.tight_layout()
        render(fig)
        st.caption(
            "A simulated p-value is itself an estimate, so it is reported with its Monte Carlo error. "
            "Raise the shuffle count above and watch the error shrink."
        )
        figure("07_permutation_d7.png", "The same test run the slow way in notebook 05: 10,000 explicit shuffles")

    with t3:
        st.subheader("What a product team actually wants to know")
        st.markdown(
            """
A p-value cannot say "the probability that gate_40 is better". A Beta-Binomial posterior can. Start from
a prior over each group's true retention rate, update it with the observed counts, and read the answer
off the posterior difference.
            """
        )
        c1, c2 = st.columns([2, 3])
        with c1:
            prior_a = st.slider("Prior alpha (pseudo-successes)", 1.0, 200.0, 1.0, 1.0)
            prior_b = st.slider("Prior beta (pseudo-failures)", 1.0, 800.0, 1.0, 1.0)
            draws = st.select_slider("Posterior draws", [20000, 50000, 100000, 200000], value=100000)
            st.caption("Beta(1, 1) is the flat prior used in the notebook: every rate from 0% to 100% equally plausible.")
        bay = bayes_compare(X_A7, N_A, X_B7, N_B, prior_a, prior_b, draws)
        with c2:
            cards([
                ("P(gate_40 truly better)", f"{100 * bay['prob_b_better']:.2f}%", "posterior probability"),
                ("Expected loss · ship gate_40", f"{100 * bay['loss_b']:.3f} pp", "average D7 given up if wrong"),
                ("Expected loss · keep gate_30", f"{100 * bay['loss_a']:.3f} pp", "average D7 given up if wrong"),
            ])
            st.write("")
            st.metric("95% credible interval",
                      f"{100 * bay['cred_low']:.3f} to {100 * bay['cred_high']:.3f} pp")
        fig, ax = plt.subplots(figsize=(9, 3.6))
        lo = min(bay["post_a"].min(), bay["post_b"].min()) * 100
        hi = max(bay["post_a"].max(), bay["post_b"].max()) * 100
        grid = np.linspace(lo, hi, 400)
        for arr, colour, name in ((bay["post_a"], C_CONTROL, "gate_30"), (bay["post_b"], C_TREAT, "gate_40")):
            dens = stats.gaussian_kde(arr * 100)(grid)
            ax.plot(grid, dens, color=colour, linewidth=2, label=name)
            ax.fill_between(grid, dens, color=colour, alpha=0.18)
        ax.legend(frameon=False, labelcolor=C_INK_SOFT, fontsize=10)
        ax.set_yticks([])
        style_axes(ax, xlabel="True D7 retention (%)", title="Posterior belief about each group's true rate")
        fig.tight_layout()
        render(fig)
        st.info(
            "**Expected loss is the decision-friendly number.** Shipping gate_40 costs about 0.82 pp of D7 "
            "retention on average if that choice is wrong; keeping gate_30 costs essentially nothing. "
            "That asymmetry, not the p-value, is what makes this an easy call."
        )
        st.markdown(
            "**Credible vs confidence interval.** A credible interval says there is a 95% probability the true "
            "difference lies inside it, given data and prior. A confidence interval makes a statement about the "
            "procedure, not this interval. With a flat prior and 90,189 players the two land on top of each other - "
            "raise the prior sliders to see how much evidence it takes to move the posterior at all."
        )
        figure("08_bayes_posterior_d7.png", "The notebook version: posteriors from 200,000 draws with a Beta(1, 1) prior")

# ==================================================================================
# 7 - Engagement
# ==================================================================================
elif page == PAGES[6]:
    st.title("Engagement: did players play differently?")
    st.markdown(
        """
        <div class="hero">
          <h2>Short answer: no - and the long answer is a lesson about means</h2>
          <p>Game rounds are extremely skewed, and exactly one impossible value sits in the control group.
          Watching what that single row does to each statistic is the most transferable thing in this project:
          revenue, playtime and session metrics all behave this way.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    include_outlier = st.toggle("Include the physically impossible 49,854-round player", value=True)
    view = ENGAGEMENT if include_outlier else ENGAGEMENT[ENGAGEMENT["series"] != "gate_30 (all)"]
    st.dataframe(view, hide_index=True, width="stretch")

    ctrl_mean = 52.46 if include_outlier else 51.34
    ctrl_std = 256.72 if include_outlier else 102.06
    cards([
        ("gate_30 mean rounds", f"{ctrl_mean:.2f}", "with the row" if include_outlier else "row excluded"),
        ("gate_30 standard deviation", f"{ctrl_std:.2f}", "one row moves it by 2.5x"),
        ("gate_30 median", "17", "does not move at all"),
        ("gate_40 mean rounds", "51.30", "unchanged by the toggle"),
    ])
    st.markdown(
        """
Toggling one row out of 44,700 cuts the control group's standard deviation from **256.72 to 102.06**,
while the median, the 90th percentile and the 99th percentile do not move by a single round. That is the
whole argument for robust statistics in one comparison - and the reason the mean was never the deciding
number here.
        """
    )

    st.divider()
    st.subheader("Four ways of asking the same question")
    st.dataframe(ENGAGEMENT_TESTS, hide_index=True, width="stretch")
    st.markdown(
        """
- **Welch's t-test is not "wrong" here** - with 45,000 players per group the sample means behave normally.
  The problem is that the mean is a poor summary of this metric, so a correct test of a bad statistic
  still produces a misleading headline.
- **Mann-Whitney sits right on the line** (p = 0.0502) with a negligible effect size: a random gate_40 player
  out-plays a random gate_30 player 49.62% of the time, where 50% is no difference at all.
- It is often called a test of medians. That is only true when the two distributions share a shape;
  in general it tests whether one group tends to produce larger values.
- **Rounds were never a ship criterion**, so a borderline result here does not move the recommendation.
        """
    )

    st.divider()
    st.subheader("The most interesting chart in the project")
    figure("09_rounds_stop_points.png", "Share of each group stopping at each exact rounds value, 20 to 60")
    st.markdown(
        """
From roughly **33 to 44 rounds the gate_30 line sits clearly above gate_40**. The natural reading is that
many gate_30 players stop shortly after hitting the level-30 gate, and gate_40 players do not, because for
them nothing is there yet.

**Present it as a pattern, not a proof.** Rounds are not levels: players replay levels and fail them, so a
player at 35 rounds is not necessarily at level 35. The chart is consistent with the gate causing the
cluster; it cannot establish it.
        """
    )
    c1, c2 = st.columns(2)
    with c1:
        figure("10_rounds_boxplot.png", "Rounds per version on a log scale")
    with c2:
        st.markdown("**Retention by rounds bucket - descriptive only**")
        st.dataframe(ROUNDS_BUCKETS, hide_index=True, width="stretch")
        st.error(
            "**Do not compare the versions inside these buckets.** Rounds happen after assignment and the "
            "gate changes them, so the buckets hold different kinds of players in each group. Page 8 shows "
            "exactly how badly that goes."
        )

# ==================================================================================
# 8 - Pitfalls
# ==================================================================================
elif page == PAGES[7]:
    st.title("Two pitfalls, demonstrated rather than asserted")
    st.markdown(
        """
        <div class="hero">
          <h2>Knowing what not to do is the job</h2>
          <p>Both pitfalls below are shown twice: once on the real data, and once in a simulation where the
          true answer is known by construction - so the bias can be measured, not just described.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Pitfall 1 · Filtering on something the treatment changed")
    a, b = st.columns([3, 2])
    with a:
        st.markdown(
            """
The tempting argument: *"only players who reached 40 rounds could have experienced both gates, so compare
those."* It sounds like a fairer comparison. It is a broken one.

Rounds played happen **after** assignment, and the gate itself changes them. Filtering on rounds therefore
selects a different kind of player in each group, and the comparison stops being about the gate.
            """
        )
        st.dataframe(PITFALL_FILTER, hide_index=True, width="stretch")
        st.error(
            f"Valid estimate: **{100 * D7['diff']:.2f} pp**. After the filter: **-1.781 pp** - "
            "more than twice as large, and no longer causal."
        )
    with b:
        fig, ax = plt.subplots(figsize=(5.6, 3.6))
        labels = ["All randomised\nplayers (valid)", "Only 40+ rounds\n(invalid)"]
        vals = [100 * D7["diff"], -1.781]
        bars = ax.bar(labels, vals, color=[C_CONTROL, C_BAD], width=0.55)
        for bar, v in zip(bars, vals):
            ax.annotate(f"{v:.2f} pp", (bar.get_x() + bar.get_width() / 2, v),
                        xytext=(0, -16 if v < 0 else 6), textcoords="offset points",
                        ha="center", color=C_INK, fontsize=10, fontweight="bold")
        ax.axhline(0, color=C_INK, linewidth=1.2)
        style_axes(ax, ylabel="Measured D7 effect (pp)")
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        render(fig)

    with st.expander("The simulation where the true effect is known to be zero", expanded=True):
        st.markdown(
            f"""
200,000 simulated players. A hidden trait - call it enjoyment - drives both retention and rounds played.
The treatment is built to make **everyone play 25% more rounds and to change retention by exactly nothing**.

| Measurement | Result |
|---|---|
| True effect on retention, all players | **{PITFALL_SIM['true_effect_pp']:+.2f} pp** (zero, as constructed) |
| Effect after filtering to 40+ rounds | **{PITFALL_SIM['filtered_effect_pp']:+.3f} pp** (invented by the filter) |

Why the fake effect appears: the extra rounds push **low-enjoyment** players over the 40-round line in the
treatment group. Those players retain poorly. So the filtered treatment group is stuffed with weaker
players, and retention there looks worse - with no causal effect anywhere in the simulation.

This is why every retention number in this project uses all randomised players, and why there is no
segment analysis by behaviour.
            """
        )

    st.divider()
    st.subheader("Pitfall 2 · Peeking at the results every day")
    st.markdown(
        """
Every extra look is another chance for noise to cross the line. The cleanest way to measure it is an
**A/A test**: both groups get the identical experience, so *every* significant result is a false positive.
Run 2,000 of them and count.
        """
    )
    c1, c2 = st.columns([2, 3])
    with c1:
        n_days = st.slider("Days the test runs (one look per day)", 3, 30, 14)
        n_exp = st.select_slider("A/A experiments to simulate", [500, 1000, 2000, 5000], value=2000)
        per_day = st.select_slider("New players per group per day", [1000, 3000, 5000, 10000], value=3000)
        rate = st.slider("True retention rate in both groups (%)", 5.0, 50.0, 19.0, 0.5) / 100
    max_z, final_z = peeking_simulation(n_exp, n_days, per_day, rate, seed=99)
    z_crit = stats.norm.ppf(0.975)
    fpr_once = float(np.mean(final_z > z_crit))
    fpr_daily = float(np.mean(max_z > z_crit))
    boundary = float(np.quantile(max_z, 0.95))
    check_max, _ = peeking_simulation(n_exp, n_days, per_day, rate, seed=12345)       # a FRESH set, never used to calibrate
    fpr_fixed = float(np.mean(check_max > boundary))
    with c2:
        cards([
            ("Checked once, at the end", f"{fpr_once:.3f}", "what alpha = 0.05 promises"),
            (f"Checked daily for {n_days} days", f"{fpr_daily:.3f}", "the cost of peeking"),
            ("Calibrated boundary", f"|z| > {boundary:.3f}", "instead of 1.96"),
            ("Boundary on fresh sims", f"{fpr_fixed:.3f}", "back near 0.05"),
        ])
        fig, ax = plt.subplots(figsize=(8, 3.4))
        names = ["Check once", f"Check daily ({n_days} looks)", "Daily + calibrated boundary"]
        vals = [fpr_once, fpr_daily, fpr_fixed]
        bars = ax.bar(names, vals, color=[C_CONTROL, C_BAD, C_GOOD], width=0.55)
        ax.axhline(0.05, color=C_INK, linestyle="--", linewidth=1.2)
        ax.annotate("promised 5%", (2.42, 0.05), xytext=(0, 6), textcoords="offset points",
                    ha="right", color=C_INK_SOFT, fontsize=9)
        for bar, v in zip(bars, vals):
            ax.annotate(f"{v:.3f}", (bar.get_x() + bar.get_width() / 2, v), xytext=(0, 5),
                        textcoords="offset points", ha="center", color=C_INK, fontsize=10, fontweight="bold")
        style_axes(ax, ylabel="False positive rate")
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        render(fig)
    st.markdown(
        f"""
With {n_days} daily looks the false-positive rate runs at about **{fpr_daily:.1%}** instead of 5%. Roughly
one in {max(1, round(1 / max(fpr_daily, 1e-9)))} "wins" found that way would be imaginary.

**The fix is a stricter boundary, honestly validated.** The threshold is calibrated on one set of
simulations and then tested on a **fresh** set - checking a rule against the data used to build it always
flatters it. Real experimentation platforms use formal sequential methods built on this idea.
        """
    )
    st.caption(
        "Simplification worth naming: in reality D7 retention for players who installed today is not known "
        "for another seven days. The simulation ignores that lag to keep the mechanism visible."
    )
    figure("11_peeking_simulation.png", "The notebook version: one A/A p-value path, and the three false-positive rates")

# ==================================================================================
# 9 - Decision log
# ==================================================================================
elif page == PAGES[8]:
    st.title("Every decision, and the alternative it beat")
    st.markdown(
        """
        <div class="hero">
          <h2>An analysis is a chain of judgement calls</h2>
          <p>Each row below is a choice that could reasonably have gone the other way. The rejected
          alternative is named next to it, because "what did you decide not to do, and why" is the question
          that separates a method from a result.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    only_preregistered = st.toggle("Show only the decisions fixed before any data was analysed", value=False)
    view = DECISIONS[DECISIONS["Where"] == "Pre-analysis plan"] if only_preregistered else DECISIONS

    for _, row in view.iterrows():
        with st.expander(f"**{row['Decision']}**  ·  {row['Where']}"):
            st.markdown(f"**Why:** {row['Why']}")
            st.markdown(f"**Rejected:** {row['Alternative rejected']}")

    st.divider()
    st.subheader("The order things happened in")
    st.markdown(
        """
1. **Plan written and committed** - hypotheses, primary metric, alpha, practical threshold, decision rules.
2. **SQL exploration** - structure, counts, retention summary, percentiles.
3. **Cleaning** - flags added, nothing deleted.
4. **Validity** - SRM and power, still before any outcome test.
5. **Primary test** - once, on the pre-registered metric.
6. **Robustness** - bootstrap, permutation, Bayesian.
7. **Engagement and pitfalls** - understanding, never ship criteria.
8. **Memo** - the decision the rules already implied.

The commit history preserves that order, which is the point of writing the plan down first.
        """
    )
    st.info(
        "**Honest caveat, stated in the README too:** this is a public dataset whose results are widely "
        "discussed online. The plan was written first to practise the discipline, not because the outcome "
        "was genuinely unknowable."
    )

# ==================================================================================
# 10 - Analyze your own test
# ==================================================================================
elif page == PAGES[9]:
    st.title("Analyze your own test")
    st.caption("The same machinery this project used, pointed at any two-group conversion test.")

    source = st.radio("Data source", ["Cookie Cats (preloaded)", "Enter my own numbers"], horizontal=True)

    if source == "Cookie Cats (preloaded)":
        metric = st.selectbox("Metric", ["D7 retention", "D1 retention"])
        col = "d7_retained" if metric == "D7 retention" else "d1_retained"
        label_a, label_b = "gate_30 (control)", "gate_40 (treatment)"
        n_a, x_a, n_b, x_b = N_A, int(CTRL[col]), N_B, int(TRT[col])
    else:
        metric, label_a, label_b = "Conversion", "Control (A)", "Treatment (B)"
        c1, c2 = st.columns(2)
        n_a = c1.number_input("Users in A", min_value=1, value=10000, step=100)
        x_a = c1.number_input("Conversions in A", min_value=0, value=1200, step=10)
        n_b = c2.number_input("Users in B", min_value=1, value=10000, step=100)
        x_b = c2.number_input("Conversions in B", min_value=0, value=1300, step=10)

    s1, s2 = st.columns(2)
    alpha = s1.selectbox("Significance level (alpha)", [0.01, 0.05, 0.10], index=1)
    intended_share_b = s2.slider("Intended share of users in B", 0.05, 0.95, 0.50, 0.05)

    if x_a > n_a or x_b > n_b:
        st.error("Conversions cannot be larger than users. Please fix the inputs.")
        st.stop()

    total = n_a + n_b
    srm_p = float(stats.chisquare([n_a, n_b], f_exp=[total * (1 - intended_share_b), total * intended_share_b]).pvalue)
    srm_banner(srm_p)

    r = ab_test(x_a, n_a, x_b, n_b, alpha)
    bay = bayes_compare(int(x_a), int(n_a), int(x_b), int(n_b), 1.0, 1.0, 100000)

    cards([
        (f"{metric} · {label_a}", f"{100 * r['rate_a']:.2f}%", f"{int(x_a):,} of {int(n_a):,}"),
        (f"{metric} · {label_b}", f"{100 * r['rate_b']:.2f}%", f"{100 * r['diff']:+.2f} pp"),
        ("p-value (two-sided z-test)", f"{r['p']:.4f}", f"z = {r['z']:.3f}"),
        ("P(B is better) · Bayesian", f"{100 * bay['prob_b_better']:.1f}%", "Beta(1, 1) prior"),
    ])

    st.write("")
    render(ci_chart([{"metric": metric, "diff_pp": 100 * r["diff"], "ci_low_pp": 100 * r["ci_low"],
                      "ci_high_pp": 100 * r["ci_high"], "primary": True}], 0.5, r["confidence"]))

    st.subheader("Verdict")
    ci_text = (f"The {r['confidence']}% confidence interval for B − A runs from "
               f"{100 * r['ci_low']:.2f} to {100 * r['ci_high']:.2f} percentage points.")
    if r["p"] < alpha and r["diff"] < 0:
        st.markdown(f"**{label_b} performs significantly worse** than {label_a} "
                    f"({100 * r['diff']:+.2f} pp, {100 * r['relative']:+.1f}% relative). {ci_text}")
    elif r["p"] < alpha and r["diff"] > 0:
        st.markdown(f"**{label_b} performs significantly better** than {label_a} "
                    f"({100 * r['diff']:+.2f} pp, {100 * r['relative']:+.1f}% relative). {ci_text}")
    else:
        st.markdown(f"**No statistically significant difference** at alpha = {alpha}. {ci_text} "
                    "The data cannot rule out effects anywhere inside that range.")
    st.markdown(f"Expected loss if you ship B: **{100 * bay['loss_b']:.3f} pp**. "
                f"Expected loss if you keep A: **{100 * bay['loss_a']:.3f} pp**.")

    with st.expander("How these numbers are calculated"):
        st.markdown(
            "- **SRM check:** chi-square goodness-of-fit test of observed users against the intended split.\n"
            "- **z-test:** pooled standard error, under the null hypothesis of no difference.\n"
            "- **Confidence interval:** unpooled (Wald) standard error around the observed difference.\n"
            "- **Bayesian:** Beta(1, 1) prior updated with the data; 100,000 posterior draws per group.\n"
            "- **Expected loss:** the average amount of the metric given up if your choice turns out to be the worse one."
        )

# ==================================================================================
# 11 - Plan a test
# ==================================================================================
elif page == PAGES[10]:
    st.title("Plan a test before you run it")
    st.caption("Fix the sample size in advance. Page 8 shows what happens to teams who do not.")

    c1, c2 = st.columns(2)
    baseline_pct = c1.number_input("Baseline rate (%)", min_value=0.1, max_value=99.9, value=19.0, step=0.1)
    mde_input = c1.number_input("Minimum detectable effect (percentage points)", min_value=0.05,
                                max_value=50.0, value=0.5, step=0.05)
    plan_alpha = c2.selectbox("Significance level", [0.01, 0.05, 0.10], index=1, key="plan_alpha")
    plan_power = c2.selectbox("Power", [0.70, 0.80, 0.90], index=1)
    daily_users = c2.number_input("New users per group per day", min_value=1, value=3000, step=100)

    p1 = baseline_pct / 100
    if p1 - mde_input / 100 <= 0:
        st.error("The MDE is larger than the baseline rate. Lower the MDE.")
        st.stop()

    n_needed = sample_size_per_group(p1, mde_input / 100, plan_alpha, plan_power)
    days_needed = n_needed / daily_users
    cards([
        ("Users needed per group", f"{int(np.ceil(n_needed)):,}", f"{2 * int(np.ceil(n_needed)):,} in total"),
        ("Days needed", f"{np.ceil(days_needed):.0f}", f"at {int(daily_users):,} per group per day"),
        ("Detectable relative change", f"{mde_input / baseline_pct * 100:.2f}%", "of the baseline rate"),
    ])

    st.divider()
    st.subheader("The cost of chasing smaller effects")
    fig, ax = plt.subplots(figsize=(9, 4))
    mdes = np.linspace(0.1, max(2.0, mde_input * 2), 200)
    ns = [sample_size_per_group(p1, m / 100, plan_alpha, plan_power) for m in mdes]
    ax.plot(mdes, ns, color=C_CONTROL, linewidth=2)
    ax.axvline(mde_input, color=C_TREAT, linestyle="--", linewidth=1.5)
    ax.annotate(f"{int(np.ceil(n_needed)):,} per group", (mde_input, n_needed),
                xytext=(12, 10), textcoords="offset points", color=C_INK, fontsize=10, fontweight="bold")
    ax.set_yscale("log")
    style_axes(ax, xlabel="Minimum detectable effect (pp)", ylabel="Users needed per group (log scale)",
               title="Halving the effect you want to catch roughly quadruples the sample")
    fig.tight_layout()
    render(fig)

    st.info(
        "**Decide the sample size before the test starts and analyse once at the end.** If the team must "
        "look early, use a sequential method with a stricter boundary - page 8 calibrates one and validates "
        "it on fresh simulations."
    )
    st.markdown(
        f"""
For context, this experiment ran with about **{int((N_A + N_B) / 2):,} players per group**. That is enough
to detect a **{mde_pp(D7['rate_a'], (N_A + N_B) / 2):.2f} pp** change in D7 at 80% power - and not enough to
reliably detect the 0.5 pp change the plan called meaningful.
        """
    )

# ==================================================================================
# 12 - Method and reproducibility
# ==================================================================================
else:
    st.title("Method and reproducibility")
    st.markdown(
        """
        <div class="hero">
          <h2>Everything here regenerates from the raw CSV</h2>
          <p>Seven notebooks run in order, each reading what the previous one wrote. Every result prints a
          checkpoint next to it, so a rerun can be verified number by number rather than trusted.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Pipeline")
    st.markdown(
        """
| Step | What it does | Tools |
|---|---|---|
| Pre-analysis plan | Hypotheses, metrics, alpha, threshold and decision rules, committed first | Markdown, Git |
| `01_sql_exploration` | Data quality, group sizes, retention summary, percentiles, buckets - CTEs, window functions, INNER and CROSS JOINs | DuckDB |
| `02_cleaning_eda` | Flags the impossible value, zero-round players and inconsistent rows; distribution charts | pandas, seaborn |
| `03_experiment_validity_power` | SRM plus per-decile diagnostic, MDE, sample size, power curve | SciPy, statsmodels |
| `04_retention_tests` | z-tests by hand, cross-checked with statsmodels and chi-square; Wald CIs; Holm | SciPy, statsmodels |
| `05_bootstrap_permutation_bayesian` | 10,000 resamples, 10,000 shuffles plus 2,000,000 exact draws, Beta-Binomial posteriors | NumPy |
| `06_engagement_tests` | Welch with and without the outlier, Mann-Whitney, bootstrap medians, winsorising | SciPy |
| `07_pitfalls_simulations` | Post-treatment filtering bias and peeking, with a calibrated boundary | NumPy |
| This app | An interactive read of all of it | Streamlit |
        """
    )

    st.subheader("How results were verified, not just produced")
    st.markdown(
        """
- Every z-test is computed from the formula **and** confirmed by statsmodels **and** by a 2x2 chi-square
  (which must equal z squared exactly).
- The MDE is derived by hand and confirmed with `statsmodels.stats.power`.
- Retention rates come out of **both** SQL and pandas, and must agree.
- The permutation p-value is produced two independent ways: explicit shuffling, and hypergeometric draws.
- The peeking boundary is calibrated on one simulation set and validated on a **fresh** one.
- Formula-based results reproduce exactly; simulated values move slightly with library versions and are
  reported with their simulation error.
        """
    )

    st.subheader("Reproduce it")
    st.code(
        "git clone <this repository>\n"
        "python -m venv .venv && .venv/Scripts/activate      # Windows\n"
        "pip install -r requirements.txt\n"
        "# download cookie_cats.csv from Kaggle into data/raw/\n"
        "# run notebooks 01 to 07 in order\n"
        "streamlit run app/streamlit_app.py",
        language="bash",
    )

    st.subheader("What this app reads")
    st.markdown(
        f"""
Only files that are committed to the repository:

- `data/processed/summary_by_version.csv` - four numbers per group ({N_A:,} / {X_A1:,} / {X_A7:,} and
  {N_B:,} / {X_B1:,} / {X_B7:,}). Every live calculation on every page is built from these.
- `reports/figures/*.png` - the 11 charts the notebooks saved.

The raw player-level file is **not** committed, and the app never needs it. Results that require the full
dataset - the engagement statistics and the simulation outputs - are carried as constants and labelled with
the notebook that produced them.
        """
    )

    st.subheader("Limitations worth repeating")
    st.markdown(
        """
- The intended allocation ratio is undocumented, so the SRM test assumes a 50/50 design.
- No revenue or purchase data, even though gates are a monetisation lever.
- The measurement window for `sum_gamerounds` is unclear - one week or 14 days, depending on the source.
- No install dates, so no time-trend or novelty check.
- No pre-assignment player attributes, so no fair segmentation - and rounds played cannot substitute.
- The test could only reliably detect D7 changes of about 0.73 pp or larger.
        """
    )
    st.caption("Full write-ups: reports/pre_analysis_plan.md and reports/decision_memo.md in the repository.")
