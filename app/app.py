"""SNHU Degree Mapper — BI Dashboard  (main / Overview page)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from data_loader import (
    profile, credit_summary, cpl_credits_by_cert,
    sophia_mapping, policies, ba_it_coverage,
)

st.set_page_config(
    page_title="SNHU Degree Mapper",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
prof = profile()
with st.sidebar:
    st.markdown("### 👤 Paulo Demestri")
    st.caption("Boca Raton, FL")
    st.markdown("---")
    st.markdown("**Goal Path**")
    st.markdown("```\nBA in IT → MS Cybersecurity\n```")
    st.markdown("---")
    st.caption("🇺🇸 EN  🇧🇷 PT  🇪🇸 ES")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🎓 SNHU Degree Mapper")
st.markdown("**Personal BI dashboard** — credit portfolio, progress tracker, cost forecast, and path simulator.")
st.markdown("---")

# ── Key Metrics ───────────────────────────────────────────────────────────────
cs = credit_summary()
pol = policies()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Transfer Credits", f"{cs['capped_at_90']}/90", help="Capped at SNHU's 90-credit maximum")
col2.metric("Remaining at SNHU", f"{cs['remaining_at_snhu']} cr", help="Credits needed to complete BA in IT")
col3.metric("CPL Credits", f"{cs['certifications']} cr", help="From eligible certifications")
col4.metric("WES Potential", f"{cs['education_wes']} cr", help="From Estácio degree — subject to WES evaluation")
col5.metric("Sophia Credits", f"{cs['sophia']} cr", help="Via Sophia Learning partnership")

st.markdown("---")

# ── Progress Bar ──────────────────────────────────────────────────────────────
pct = cs["capped_at_90"] / cs["ba_it_total"]
st.subheader("BA in IT — Overall Progress")
st.progress(pct, text=f"{cs['capped_at_90']} of {cs['ba_it_total']} credits covered ({pct:.0%})")

c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Credit Portfolio Breakdown")
    breakdown = {
        "CPL — Certifications": cs["certifications"],
        "WES — Estácio Degree": cs["education_wes"],
        "Sophia Learning": cs["sophia"],
    }
    df_break = pd.DataFrame(
        list(breakdown.items()), columns=["Source", "Credits"]
    )
    df_break["% of Total Potential"] = (df_break["Credits"] / cs["total_potential"] * 100).round(1)
    st.dataframe(df_break, use_container_width=True, hide_index=True)

    over_cap = cs["total_potential"] - cs["capped_at_90"]
    if over_cap > 0:
        st.info(
            f"**+{over_cap} credits above cap.** Your credentials ({cs['total_potential']} cr) "
            f"exceed SNHU's 90-credit transfer limit. You've already maximised transfer — "
            f"only {cs['remaining_at_snhu']} credits remain at SNHU."
        )

with c2:
    st.subheader("🗺️ Degree Roadmap")
    st.markdown("""
| Phase | Action | Duration | Cost |
|-------|--------|----------|------|
| **Now → Month 2** | WES evaluation + Sophia Learning | 2–3 months | ~$482 |
| **Month 2** | Submit CPL request to SNHU | 1 week | $0 |
| **Month 3** | Complete CompTIA Security+ | 1 month | ~$400 |
| **Month 4** | Enroll in BA in IT at SNHU | — | — |
| **Month 4–14** | Complete 30 remaining credits | ~10 months | ~$9,900 |
| **Month 14** | Bachelor's complete ✅ | — | — |
| **Month 14–26** | MS in Cybersecurity (36 cr) | ~12 months | ~$22,932 |
| **Parallel** | PUC Minas AI/ML (2025–2027) | — | — |
""")

st.markdown("---")

# ── BA IT Course Coverage Summary ─────────────────────────────────────────────
st.subheader("📚 BA in IT — Course Coverage Snapshot")
coverage = ba_it_coverage()
df_cov = pd.DataFrame(coverage)
covered_count = df_cov["covered"].sum()
total_count = len(df_cov)

c1, c2, c3 = st.columns(3)
c1.metric("Major Courses Covered", f"{covered_count}/{total_count}")
c2.metric("Still Needed at SNHU", f"{total_count - covered_count}")
c3.metric("Est. Cost (remaining courses)", f"${(total_count - covered_count) * 3 * 330:,}")

st.caption("See **BA IT Progress** page for full course-by-course breakdown.")

st.markdown("---")

# ── Cost Summary ──────────────────────────────────────────────────────────────
st.subheader("💰 Total Cost Estimate")
cost_data = {
    "Item": [
        "WES Evaluation",
        "Sophia Learning (3 months)",
        "SNHU — BA in IT (30 cr × $330)",
        "SNHU — MS Cybersecurity (36 cr × $637)",
        "**TOTAL**",
    ],
    "Cost": ["$185", "$297", "$9,900", "$22,932", "**$33,314**"],
}
st.table(pd.DataFrame(cost_data))
st.caption("Compared to a traditional 4-year US private university: $120K–$200K. Paulo reaches MS level in ~26 months for ~$33K.")

st.markdown("---")
st.caption("Data sources: SNHU Kuali catalog API · WES evaluation · Sophia Learning partner guide · Personal profile")
