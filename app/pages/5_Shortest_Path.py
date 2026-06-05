"""Shortest Path Simulator — Compare degree sequences and milestones."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import credit_summary, policies, ms_cyb_curriculum, ms_it_curriculum

st.set_page_config(page_title="Shortest Path", page_icon="⚡", layout="wide")
st.title("⚡ Shortest Path Simulator")
st.markdown("Simulate different credit combinations and compare time-to-degree for each master's option.")

cs = credit_summary()
pol = policies()

# ── MS program comparison ──────────────────────────────────────────────────────
st.subheader("🎓 MS Program Comparison")

ms_cyb = pol["ms_cybersecurity"]
ms_it = pol["ms_it_it_concentration"]

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🔐 MS in Cybersecurity *(Recommended)*")
    st.metric("Fit Score", f"{ms_cyb['paulo_fit_score']}/10")
    st.metric("Total Credits", ms_cyb["total_credits"])
    st.metric("Max Transfer Credits", ms_cyb["max_transfer_credits"])
    st.metric("Cost (full, no transfer)", f"${ms_cyb['total_cost_usd']:,}")
    st.metric("Est. Duration (full time)", f"{ms_cyb['est_months_full_time']} months")
    st.markdown("**Curriculum:**")
    df_cyb = pd.DataFrame(ms_cyb_curriculum()).drop_duplicates(subset=["code"])
    st.dataframe(df_cyb.rename(columns={"code": "Code", "title": "Course", "credits_text": "Credits"}),
                 use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### 💻 MS in IT — IT Concentration")
    st.metric("Fit Score", f"{ms_it['paulo_fit_score']}/10")
    st.metric("Total Credits", ms_it["total_credits"])
    st.metric("Max Transfer Credits", ms_it["max_transfer_credits"])
    st.metric("Cost (full, no transfer)", f"${ms_it['total_cost_usd']:,}")
    st.metric("Est. Duration (full time)", f"{ms_it['est_months_full_time']} months")
    st.markdown("**Curriculum:**")
    df_it = pd.DataFrame(ms_it_curriculum()).drop_duplicates(subset=["code"])
    st.dataframe(df_it.rename(columns={"code": "Code", "title": "Course", "credits_text": "Credits"}),
                 use_container_width=True, hide_index=True)

st.info(ms_it["comparison_vs_ms_cybersecurity"])

# ── BA → MS transfer policy ───────────────────────────────────────────────────
st.markdown("---")
st.subheader("📌 BA in IT → MS Transfer Policy")
ba_ms = pol["ba_it_to_ms_transfer"]
st.error(f"**{ba_ms['question']}**\n\n{ba_ms['answer']}\n\n{ba_ms['detail']}")

puc = ba_ms["paulo_graduate_credit_potential"]
st.success(
    f"**PUC Minas opportunity:** {puc['source']}\n\n"
    f"{puc['note']}\n\n"
    f"Estimated: {puc['estimated_credits']}"
)

# ── Interactive path simulator ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("🎛️ Path Simulator")

col1, col2 = st.columns(2)
with col1:
    target_ms = st.radio("Target Master's", ["MS Cybersecurity", "MS IT — IT Concentration"])
with col2:
    grad_transfer = st.slider("Graduate transfer credits (PUC Minas)", 0, 12, 0, 3)

courses_per_term = st.slider("Courses per 8-week term", 1, 3, 2)
weeks_between_programs = st.slider("Weeks between BA completion and MS start", 0, 12, 4)

# Calculations
ba_remaining = cs["remaining_at_snhu"]
ms_total = 36
ms_needed = ms_total - grad_transfer
ms_credits_per_term = courses_per_term * 3

ba_terms = -(-ba_remaining // (courses_per_term * 3))  # ceiling division
ms_terms = -(-ms_needed // ms_credits_per_term)

ba_months = int(ba_terms * 2)  # 8-week terms
gap_months = round(weeks_between_programs / 4.3)
ms_months = int(ms_terms * 2)
total_months = ba_months + gap_months + ms_months

# Timeline milestones
from datetime import date
from dateutil.relativedelta import relativedelta

today = date.today()
sophia_done = today + relativedelta(months=3)
ba_start = today + relativedelta(months=4)
ba_done = ba_start + relativedelta(months=ba_months)
ms_start = ba_done + relativedelta(weeks=weeks_between_programs)
ms_done = ms_start + relativedelta(months=ms_months)

milestones = [
    {"Milestone": "Start Sophia Learning + WES", "Date": today.strftime("%B %Y"), "Month": 0},
    {"Milestone": "Sophia Learning complete (30 cr)", "Date": sophia_done.strftime("%B %Y"), "Month": 3},
    {"Milestone": "Enroll in BA in IT at SNHU", "Date": ba_start.strftime("%B %Y"), "Month": 4},
    {"Milestone": "✅ BA in IT complete", "Date": ba_done.strftime("%B %Y"), "Month": 4 + ba_months},
    {"Milestone": f"Enroll in {target_ms}", "Date": ms_start.strftime("%B %Y"), "Month": 4 + ba_months + gap_months},
    {"Milestone": f"✅ {target_ms} complete", "Date": ms_done.strftime("%B %Y"), "Month": 4 + ba_months + gap_months + ms_months},
]

df_milestones = pd.DataFrame(milestones)

st.markdown("#### 📅 Projected Timeline")
st.dataframe(df_milestones, use_container_width=True, hide_index=True)

col1, col2, col3 = st.columns(3)
col1.metric("BA in IT duration", f"{ba_months} months")
col2.metric("MS duration", f"{ms_months} months")
col3.metric("Total time to MS", f"{total_months} months", f"~{total_months/12:.1f} years")

# ── Immediate next 5 actions ───────────────────────────────────────────────────
st.markdown("---")
st.subheader("✅ Immediate Next 5 Actions")
st.markdown("""
1. **Submit WES evaluation** at wes.org (~$185 · Course-by-Course · 7 business days)
2. **Create Sophia Learning account** at sophia.org → select SNHU as destination → start English Comp I
3. **Complete CompTIA Security+** (in progress) — adds 3 credits CPL (CYB220)
4. **Email transfer@snhu.edu** with full cert list for preliminary CPL evaluation
5. **Confirm PUC Minas transcript format** — begin planning WES evaluation for graduate credits after completion
""")
