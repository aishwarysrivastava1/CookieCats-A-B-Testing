# streamlit_app.py
# A/B test analyzer and planner. Run locally with:  streamlit run app/streamlit_app.py

import numpy as np                                   # maths and random numbers
import pandas as pd                                  # reading the summary CSV
import matplotlib.pyplot as plt                      # chart for the confidence interval
import streamlit as st                               # the web app framework
from scipy import stats                              # normal distribution and chi-square test
from pathlib import Path                             # file paths that work locally and on Streamlit Cloud

# ---------------- Page setup ----------------
st.set_page_config(page_title="A/B Test Analyzer", page_icon="🧪", layout="wide")   # browser tab title, icon and wide layout
st.title("🧪 A/B Test Analyzer")                     # big heading at the top of the page
st.caption("Built on the Cookie Cats mobile game experiment (gate at level 30 vs level 40).")   # small grey subtitle

APP_DIR = Path(__file__).resolve().parent            # folder that contains this file (app/)
SUMMARY_FILE = APP_DIR.parent / "data" / "processed" / "summary_by_version.csv"   # summary table produced by notebook 04

tab_analyze, tab_plan, tab_about = st.tabs(["Analyze a test", "Plan a test", "About"])   # three tabs across the top

# ---------------- Tab 1: Analyze a test ----------------
with tab_analyze:                                    # everything indented below appears inside the first tab
    source = st.radio("Data source", ["Cookie Cats (preloaded)", "Enter my own numbers"], horizontal=True)   # choose where the numbers come from

    if source == "Cookie Cats (preloaded)":          # branch 1: use the real experiment
        summary = pd.read_csv(SUMMARY_FILE)          # load the tiny summary table
        metric = st.selectbox("Metric", ["D7 retention", "D1 retention"])   # which metric to analyze
        column = "d7_retained" if metric == "D7 retention" else "d1_retained"   # matching column name in the CSV
        control_row = summary[summary["version"] == "gate_30"].iloc[0]      # the gate_30 row
        treat_row = summary[summary["version"] == "gate_40"].iloc[0]        # the gate_40 row
        label_a = "gate_30 (control)"                # display name for group A
        label_b = "gate_40 (treatment)"              # display name for group B
        n_a = int(control_row["players"])            # players in A
        x_a = int(control_row[column])               # retained players in A
        n_b = int(treat_row["players"])              # players in B
        x_b = int(treat_row[column])                 # retained players in B
    else:                                            # branch 2: the user types their own numbers
        metric = "Conversion"                        # generic metric name
        label_a = "Control (A)"                      # display name for group A
        label_b = "Treatment (B)"                    # display name for group B
        col1, col2 = st.columns(2)                   # two input columns side by side
        n_a = col1.number_input("Users in A", min_value=1, value=10000, step=100)          # users in A
        x_a = col1.number_input("Conversions in A", min_value=0, value=1200, step=10)      # conversions in A
        n_b = col2.number_input("Users in B", min_value=1, value=10000, step=100)          # users in B
        x_b = col2.number_input("Conversions in B", min_value=0, value=1300, step=10)      # conversions in B

    settings_1, settings_2 = st.columns(2)           # two columns for test settings
    alpha = settings_1.selectbox("Significance level (alpha)", [0.01, 0.05, 0.10], index=1)        # default 0.05
    intended_share_b = settings_2.slider("Intended share of users in B", 0.05, 0.95, 0.50, 0.05)   # default 50/50 design

    if x_a > n_a or x_b > n_b:                       # conversions can never exceed users
        st.error("Conversions cannot be larger than users. Please fix the inputs.")   # show a red error box
        st.stop()                                    # stop running the rest of the script

    # ---- 1. Sample ratio mismatch check ----
    total = n_a + n_b                                # total users
    expected_counts = [total * (1 - intended_share_b), total * intended_share_b]   # counts we expected from the design
    srm_p = stats.chisquare([n_a, n_b], f_exp=expected_counts).pvalue              # chi-square goodness-of-fit p-value
    if srm_p < 0.001:                                # strict threshold used by many experimentation platforms
        st.error(f"Sample ratio mismatch detected (p = {srm_p:.5f}). Investigate assignment and logging before trusting results.")
    elif srm_p < 0.01:                               # borderline zone
        st.warning(f"Borderline sample ratio mismatch (p = {srm_p:.5f}). Results can be reported, but flag this and investigate.")
    else:                                            # no sign of a problem
        st.success(f"No sample ratio mismatch detected (p = {srm_p:.4f}).")

    # ---- 2. Frequentist two-proportion z-test ----
    rate_a = x_a / n_a                               # rate in A
    rate_b = x_b / n_b                               # rate in B
    diff = rate_b - rate_a                           # absolute difference (B minus A)
    relative = diff / rate_a if rate_a > 0 else float("nan")   # relative change; undefined if A's rate is zero
    pooled = (x_a + x_b) / (n_a + n_b)               # pooled rate assuming no difference
    se_pooled = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))   # standard error for the test
    z_stat = diff / se_pooled if se_pooled > 0 else 0.0                # z-statistic (guard against division by zero)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))                    # two-sided p-value
    se_unpooled = np.sqrt(rate_a * (1 - rate_a) / n_a + rate_b * (1 - rate_b) / n_b)   # standard error for the CI
    z_crit = stats.norm.ppf(1 - alpha / 2)           # critical value for the chosen alpha
    ci_low = diff - z_crit * se_unpooled             # lower CI bound
    ci_high = diff + z_crit * se_unpooled            # upper CI bound
    confidence = int(round((1 - alpha) * 100))       # e.g. 95 for alpha = 0.05

    # ---- 3. Bayesian Beta-Binomial ----
    rng = np.random.default_rng(seed=0)              # fixed seed so the numbers do not jump on every rerun
    draws_a = rng.beta(1 + x_a, 1 + n_a - x_a, size=100000)   # posterior draws for A's true rate
    draws_b = rng.beta(1 + x_b, 1 + n_b - x_b, size=100000)   # posterior draws for B's true rate
    prob_b_better = np.mean(draws_b > draws_a)       # chance B's true rate is higher
    loss_choose_b = np.mean(np.maximum(draws_a - draws_b, 0))  # expected loss if we ship B
    loss_choose_a = np.mean(np.maximum(draws_b - draws_a, 0))  # expected loss if we keep A

    # ---- 4. Headline numbers ----
    m1, m2, m3, m4 = st.columns(4)                   # four metric cards in a row
    m1.metric(f"{metric}: {label_a}", f"{100 * rate_a:.2f}%")                                # rate in A
    m2.metric(f"{metric}: {label_b}", f"{100 * rate_b:.2f}%", f"{100 * diff:+.2f} pp")       # rate in B with the change
    m3.metric("p-value (two-sided z-test)", f"{p_value:.4f}")                                # p-value
    m4.metric("P(B is better) - Bayesian", f"{100 * prob_b_better:.1f}%")                    # Bayesian probability

    # ---- 5. Confidence interval chart ----
    fig, ax = plt.subplots(figsize=(8, 1.8))         # short, wide chart
    ax.errorbar([100 * diff], [0], xerr=[[100 * (diff - ci_low)], [100 * (ci_high - diff)]], fmt="o", capsize=8, markersize=9)   # point with CI bar
    ax.axvline(0, color="black", linewidth=1)        # zero line = no difference
    ax.set_yticks([])                                # hide the y-axis ticks
    ax.set_xlabel(f"Difference B - A (percentage points), {confidence}% CI")   # x label
    st.pyplot(fig)                                   # render the matplotlib chart in the app
    plt.close(fig)                                   # free memory, because Streamlit reruns the script on every click

    # ---- 6. Plain-English verdict ----
    st.subheader("Verdict")                          # section heading
    ci_text = f"The {confidence}% confidence interval for B - A runs from {100 * ci_low:.2f} to {100 * ci_high:.2f} percentage points."   # CI sentence
    if p_value < alpha and diff < 0:                 # significant and B is worse
        st.markdown(f"**{label_b} performs significantly worse** than {label_a} ({100 * diff:+.2f} pp, {100 * relative:+.1f}% relative). {ci_text}")
    elif p_value < alpha and diff > 0:               # significant and B is better
        st.markdown(f"**{label_b} performs significantly better** than {label_a} ({100 * diff:+.2f} pp, {100 * relative:+.1f}% relative). {ci_text}")
    else:                                            # not significant
        st.markdown(f"**No statistically significant difference** at alpha = {alpha}. {ci_text} The data cannot rule out effects inside that range.")
    st.markdown(f"Expected loss if you ship B: **{100 * loss_choose_b:.3f} pp**. Expected loss if you keep A: **{100 * loss_choose_a:.3f} pp**.")   # decision-oriented Bayesian summary

    with st.expander("How these numbers are calculated"):   # collapsible explanation
        st.markdown(
            "- **SRM check:** chi-square goodness-of-fit test of observed users against the intended split.\n"
            "- **z-test:** pooled standard error under the null hypothesis of no difference.\n"
            "- **Confidence interval:** unpooled (Wald) standard error around the observed difference.\n"
            "- **Bayesian:** Beta(1, 1) prior updated with the data; 100,000 posterior draws per group.\n"
            "- **Expected loss:** the average amount of the metric you give up if your choice turns out to be the worse one."
        )

# ---------------- Tab 2: Plan a test ----------------
with tab_plan:                                       # everything below appears inside the second tab
    st.subheader("How many users does a test need?") # section heading
    p1_col, p2_col = st.columns(2)                   # two input columns
    baseline_pct = p1_col.number_input("Baseline rate (%)", min_value=0.1, max_value=99.9, value=19.0, step=0.1)   # current rate
    mde_pp = p1_col.number_input("Minimum detectable effect (percentage points)", min_value=0.05, max_value=50.0, value=0.5, step=0.05)   # smallest change worth detecting
    plan_alpha = p2_col.selectbox("Significance level", [0.01, 0.05, 0.10], index=1, key="plan_alpha")     # alpha (key avoids clashing with tab 1)
    plan_power = p2_col.selectbox("Power", [0.70, 0.80, 0.90], index=1)                                    # desired power
    daily_users = p2_col.number_input("New users per group per day", min_value=1, value=3000, step=100)    # traffic

    p1 = baseline_pct / 100                          # baseline as a proportion
    p2 = p1 - mde_pp / 100                           # rate after a drop equal to the MDE
    if p2 <= 0:                                      # a rate cannot go below zero
        st.error("The MDE is larger than the baseline rate. Lower the MDE.")   # error box
        st.stop()                                    # stop the script
    z_a = stats.norm.ppf(1 - plan_alpha / 2)         # critical z for alpha
    z_b = stats.norm.ppf(plan_power)                 # z for the chosen power
    n_needed = ((z_a + z_b) ** 2) * (p1 * (1 - p1) + p2 * (1 - p2)) / (p1 - p2) ** 2   # users per group
    days_needed = n_needed / daily_users             # how long the test must run

    r1, r2 = st.columns(2)                           # two result cards
    r1.metric("Users needed per group", f"{int(np.ceil(n_needed)):,}")   # formatted with commas
    r2.metric("Days needed", f"{np.ceil(days_needed):.0f}")              # rounded up to whole days
    st.info("Decide the sample size BEFORE the test starts and analyze once at the end. Checking results every day and stopping early inflates false positives.")   # key lesson

# ---------------- Tab 3: About ----------------
with tab_about:                                      # third tab
    st.markdown(
        "### About this project\n"
        "This app is part of an end-to-end analysis of the **Cookie Cats** A/B test, where the first progression gate "
        "was moved from level 30 to level 40 for a random half of new players.\n\n"
        "**Full analysis:** SQL (DuckDB), data cleaning, SRM check, power analysis, z-tests, bootstrap, permutation test, "
        "Bayesian analysis, Mann-Whitney test, and simulations of common experimentation pitfalls.\n\n"
        "**Code:** see the GitHub repository linked in the README."
    )
