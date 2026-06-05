"""Shortest Path Simulator — Compare degree sequences and milestones."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import (
    credit_summary, policies, ms_cyb_curriculum, ms_it_curriculum,
    bs_it_curriculum, wes_analysis,
)

st.set_page_config(page_title="Shortest Path", page_icon="⚡", layout="wide")
st.title("⚡ Shortest Path Simulator")
st.markdown("Simulate different credit combinations and compare time-to-degree for each master's option.")

cs = credit_summary()
pol = policies()

# ── WES vs GenEd Analysis ─────────────────────────────────────────────────────
wes_q = wes_analysis()
st.subheader("🔍 WES vs GenEd-Only: Vale a Pena?")

verdict_color = "🟢" if "WES VALE" in wes_q["verdict"] else "🔴"
st.success(f"**Veredicto: {verdict_color} {wes_q['verdict']}**")

snap = wes_q["paulo_credit_snapshot"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("CPL (Certificações)", f"{snap['cpl_certifications']} cr")
c2.metric("Sophia Learning", f"{snap['sophia_learning']} cr")
c3.metric("Subtotal atual", f"{snap['subtotal']} cr", f"{snap['gap_to_cap']} cr abaixo do cap")
c4.metric("Cap SNHU (90 cr)", f"{snap['snhu_transfer_cap']} cr", f"Faltam {snap['gap_to_cap']} cr")

col_wes, col_gen = st.columns(2)
with col_wes:
    st.markdown("#### ✅ Vantagens do WES ($185)")
    for adv in wes_q["wes_advantages"]:
        st.markdown(f"- {adv}")

with col_gen:
    st.markdown("#### ❌ Desvantagens de só GenEd")
    for dis in wes_q["gened_only_disadvantages"]:
        st.markdown(f"- {dis}")

rec = wes_q["recommendation"]
st.info(
    f"**Recomendação primária:** {rec['primary']}\n\n"
    f"**Paralelo:** {rec['secondary']}\n\n"
    f"**Resultado esperado:** {rec['expected_outcome']}\n\n"
    f"**Bottom line:** {rec['bottom_line']}"
)

# ── Bachelor's Program Comparison ────────────────────────────────────────────
st.markdown("---")
st.subheader("🎓 Comparação: BA in IT vs BS in IT (Cybersecurity)")

ba_pol = pol  # BA IT is the primary program
bs_pol = pol["bs_it_cybersecurity"]

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📘 BA in Information Technologies *(Recomendado)*")
    st.metric("Total Credits", 120)
    st.metric("Free Elective Credits", "21 cr")
    st.metric("Max Transfer", "90 cr")
    st.metric("Créditos a fazer no SNHU", f"{cs['remaining_at_snhu']} cr")
    st.metric("Custo restante", f"${cs['cost_remaining']:,}")
    st.success("Melhor para Paulo: mais espaço para créditos WES entrarem como eletivas")

with col2:
    st.markdown(f"#### 📗 BS in IT — Cybersecurity Concentration")
    st.metric("Total Credits", bs_pol["total_credits"])
    st.metric("Free Elective Credits", f"{bs_pol['free_elective_credits']} cr")
    st.metric("Max Transfer", f"{bs_pol['max_transfer_credits']} cr")
    st.metric("Créditos a fazer no SNHU", f"{cs['remaining_at_snhu']} cr")
    st.metric("Custo restante", f"${cs['cost_remaining']:,}")
    st.warning("Menos espaço para eletivas WES. Concentração em Cybersecurity é boa prep para MS.")

st.markdown("#### Diferenças chave")
for diff in bs_pol["vs_ba_it"]["key_differences"]:
    st.markdown(f"- {diff}")

st.caption(f"⚠️ Currículo BS IT baseado na estrutura publicada do programa. API SNHU inacessível neste ambiente. Verifique em [snhu.edu/admission/academic-catalogs]({bs_pol['catalog_url']})")

# ── BS IT Curriculum ──────────────────────────────────────────────────────────
with st.expander("📋 Ver Currículo BS IT (Core + Cybersecurity Concentration)"):
    df_bs = pd.DataFrame(bs_it_curriculum())
    st.dataframe(df_bs.rename(columns={"code": "Code", "title": "Course", "credits": "Credits"}),
                 use_container_width=True, hide_index=True)

# ── MS program comparison ──────────────────────────────────────────────────────
st.markdown("---")
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

ba_terms = -(-ba_remaining // (courses_per_term * 3))
ms_terms = -(-ms_needed // ms_credits_per_term)

ba_months = int(ba_terms * 2)
gap_months = round(weeks_between_programs / 4.3)
ms_months = int(ms_terms * 2)
total_months = ba_months + gap_months + ms_months

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
1. **Submit WES evaluation** at wes.org (~$185 · Course-by-Course · 7 business days) — translation já disponível
2. **Continue Sophia Learning** enquanto aguarda WES → English Comp I e Project Management (QSO340)
3. **Complete CompTIA Security+** (in progress) — adds 3 credits CPL (CYB220)
4. **Email transfer@snhu.edu** with full cert list for preliminary CPL evaluation
5. **Confirm PUC Minas transcript format** — begin planning WES evaluation for graduate credits after completion
""")
