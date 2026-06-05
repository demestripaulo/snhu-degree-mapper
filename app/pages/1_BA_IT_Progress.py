"""BA in IT — Course-by-course progress tracker."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import ba_it_coverage, ba_it_curriculum, sophia_mapping, target_certs, wes_mapping

st.set_page_config(page_title="BA IT Progress", page_icon="📚", layout="wide")
st.title("📚 BA in IT — Course Progress Tracker")
st.markdown("Track each required course and its coverage source. Toggle status as you progress.")

# ── Coverage table ─────────────────────────────────────────────────────────────
coverage = ba_it_coverage()
df = pd.DataFrame(coverage)

# ── Filter controls ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    status_filter = st.multiselect(
        "Filter by Status",
        options=df["status"].unique().tolist(),
        default=df["status"].unique().tolist(),
    )
with col2:
    source_filter = st.multiselect(
        "Filter by Source",
        options=df["source"].unique().tolist(),
        default=df["source"].unique().tolist(),
    )

filtered = df[df["status"].isin(status_filter) & df["source"].isin(source_filter)]

# ── Color code ─────────────────────────────────────────────────────────────────
def highlight(row):
    if row["covered"]:
        color = "#d4edda"  # green
    else:
        color = "#fff3cd"  # yellow
    return [f"background-color: {color}"] * len(row)

st.dataframe(
    filtered[["code", "title", "credits", "source", "status"]].style.apply(highlight, axis=1),
    use_container_width=True,
    hide_index=True,
)

# ── Summary ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Coverage Summary by Source")
summary = df.groupby("source")["credits"].sum().reset_index()
summary.columns = ["Source", "Credits"]
st.dataframe(summary, use_container_width=True, hide_index=True)

# ── Sophia highlight ───────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🎯 Sophia Learning — BA IT Mapped Courses")
sophia = sophia_mapping()
sophia_courses = sophia["courses"]
df_sophia = pd.DataFrame(sophia_courses)[[
    "sophia_course", "snhu_code", "snhu_title", "area",
    "credits", "est_weeks", "cost_usd", "priority", "notes"
]]
df_sophia = df_sophia.sort_values("priority")
df_sophia.columns = [
    "Sophia Course", "SNHU Code", "SNHU Title", "Area",
    "Credits", "Est. Weeks", "Cost $", "Priority", "Notes"
]

def highlight_priority(row):
    if row["Priority"] <= 4:
        return ["background-color: #d4edda"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_sophia.style.apply(highlight_priority, axis=1),
    use_container_width=True,
    hide_index=True,
)

high = [c for c in sophia_courses if c["priority"] <= 4]
st.success(
    f"**Start here:** {', '.join(c['sophia_course'] for c in high)} — "
    f"These 4 courses cover {sum(c['credits'] for c in high)} credits including QSO340 (a required major course)."
)

# ── CLEP alternatives ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ CLEP / DSST Exam Alternatives (Faster + Cheaper)")
clep = sophia["clep_alternatives"]
df_clep = pd.DataFrame(clep)
df_clep.columns = ["Exam", "SNHU Code", "Credits", "Cost $", "Notes"]
st.dataframe(df_clep, use_container_width=True, hide_index=True)
st.caption("CLEP exams: $93/exam at a Pearson Vue test center. No subscription needed — single payment per exam.")
