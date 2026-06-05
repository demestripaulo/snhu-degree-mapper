"""Cost Forecast — Full breakdown and scenario comparison."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import credit_summary, policies, sophia_mapping

st.set_page_config(page_title="Cost Forecast", page_icon="💰", layout="wide")
st.title("💰 Cost Forecast — Full Degree Path")

cs = credit_summary()
pol = policies()
sophia = sophia_mapping()

# ── Scenario sliders ───────────────────────────────────────────────────────────
st.subheader("🎛️ Adjust Scenario")
col1, col2, col3 = st.columns(3)

with col1:
    snhu_undergrad_rate = st.number_input(
        "SNHU undergrad $/credit", value=330, min_value=200, max_value=500, step=10
    )
with col2:
    snhu_grad_rate = st.number_input(
        "SNHU grad $/credit", value=637, min_value=400, max_value=900, step=10
    )
with col3:
    grad_transfer = st.slider(
        "Graduate transfer credits (PUC Minas)", min_value=0, max_value=12, value=0, step=3,
        help="If PUC Minas coursework is WES-evaluated and accepted by SNHU"
    )

remaining_undergrad = cs["remaining_at_snhu"]
ms_credits_needed = 36 - grad_transfer
sophia_months = sophia["summary"]["est_months"]
sophia_cost = sophia_months * 99

# ── Cost table ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Itemized Cost Breakdown")

items = [
    {"Item": "WES Course-by-Course Evaluation", "Phase": "Pre-enrollment", "Cost": 185},
    {"Item": f"Sophia Learning ({sophia_months} months × $99)", "Phase": "Pre-enrollment", "Cost": sophia_cost},
    {"Item": f"BA in IT — {remaining_undergrad} credits × ${snhu_undergrad_rate}", "Phase": "Bachelor's", "Cost": remaining_undergrad * snhu_undergrad_rate},
    {"Item": f"MS Cybersecurity — {ms_credits_needed} credits × ${snhu_grad_rate}", "Phase": "Master's", "Cost": ms_credits_needed * snhu_grad_rate},
]
if grad_transfer > 0:
    items.insert(-1, {"Item": f"Graduate transfer credits (−{grad_transfer} cr saved)", "Phase": "Master's", "Cost": -(grad_transfer * snhu_grad_rate)})

df_cost = pd.DataFrame(items)
total = df_cost["Cost"].sum()
total_row = pd.DataFrame([{"Item": "**TOTAL**", "Phase": "—", "Cost": total}])
df_display = pd.concat([df_cost, total_row], ignore_index=True)

def highlight_total(row):
    if row["Item"] == "**TOTAL**":
        return ["font-weight: bold; background-color: #e8f4f8"] * len(row)
    elif row["Cost"] < 0:
        return ["background-color: #d4edda"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_display.style.apply(highlight_total, axis=1)
    .format({"Cost": lambda x: f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}"}),
    use_container_width=True,
    hide_index=True,
)

# ── Savings vs traditional ─────────────────────────────────────────────────────
traditional_low = 120_000
traditional_high = 200_000
savings_low = traditional_low - total
savings_high = traditional_high - total

st.success(
    f"**${total:,.0f} total** vs traditional 4-year US private university ($120K–$200K). "
    f"Savings: **${savings_low:,.0f}–${savings_high:,.0f}**"
)

# ── Phase timeline ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📅 Cost by Phase & Timeline")

phases = {
    "Pre-enrollment": {"months": "0–3", "cost": 185 + sophia_cost, "note": "WES + Sophia"},
    "BA in IT at SNHU": {"months": "4–14", "cost": remaining_undergrad * snhu_undergrad_rate, "note": f"{remaining_undergrad} credits"},
    "MS Cybersecurity": {"months": "15–26", "cost": ms_credits_needed * snhu_grad_rate, "note": f"{ms_credits_needed} credits"},
}
df_phases = pd.DataFrame([
    {"Phase": k, "Timeline": v["months"], "Cost": v["cost"], "Details": v["note"]}
    for k, v in phases.items()
])
st.dataframe(df_phases.style.format({"Cost": "${:,.0f}"}), use_container_width=True, hide_index=True)

# ── Monthly cost estimate ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Monthly Cost Rate")
col1, col2 = st.columns(2)
with col1:
    ba_monthly = (remaining_undergrad * snhu_undergrad_rate) / 10
    st.metric("BA in IT (avg/month)", f"${ba_monthly:,.0f}", help="~2 courses/8-week term = ~10 months")
with col2:
    ms_monthly = (ms_credits_needed * snhu_grad_rate) / 12
    st.metric("MS Cybersecurity (avg/month)", f"${ms_monthly:,.0f}", help="~2 courses/8-week term = ~12 months")

st.caption("All figures are estimates. Verify current tuition at snhu.edu before enrolling.")
