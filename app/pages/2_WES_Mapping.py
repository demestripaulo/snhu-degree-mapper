"""WES Transfer Mapping — Estácio de Sá courses → SNHU equivalents."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import wes_mapping, policies

st.set_page_config(page_title="WES Mapping", page_icon="🗺️", layout="wide")
st.title("🗺️ WES Transfer Mapping — Estácio de Sá → SNHU")

pol = policies()
wes_pol = pol["wes_evaluation"]
time_pol = pol["transfer_credit_time_limit"]["paulo_assessment"]

# ── Policy Banner ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ SNHU Transfer Credit Time Limit Policy", expanded=True):
    verdict_color = "🟢" if time_pol["verdict"] == "ACCEPTABLE" else "🔴"
    st.markdown(f"""
**Verdict: {verdict_color} {time_pol['verdict']}**

{pol['transfer_credit_time_limit']['official_policy']}

**Paulo's assessment:** Degree from {time_pol['graduation_year']} ({time_pol['years_elapsed']} years ago).
{time_pol['rationale']}

**Potentially dated courses** (flag for advisor review):
{chr(10).join(f"- {c}" for c in time_pol['risk_courses'])}
""")

# ── WES Submission Checklist ──────────────────────────────────────────────────
with st.expander("📋 WES Submission Checklist"):
    st.markdown(f"""
- **Service:** {wes_pol['service']}
- **Cost:** ${wes_pol['cost_usd']} (Course-by-Course evaluation)
- **Processing:** {wes_pol['processing_days_basic']} (rush) / {wes_pol['processing_days_standard']} (standard)
- **Evaluation type to order:** {wes_pol['what_to_order']}

**Documents needed:**
""")
    for doc in wes_pol["documents_required"]:
        st.markdown(f"  - ✅ {doc}")
    st.success(wes_pol["note"])

st.markdown("---")

# ── Course mapping table ───────────────────────────────────────────────────────
wes = wes_mapping()
df = pd.DataFrame(wes)

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    status_opts = ["All"] + sorted(df["pdf_status"].dropna().unique().tolist())
    sel_status = st.selectbox("Filter by Status", status_opts)
with col2:
    usable_opts = ["All", "WES Usable", "Not Usable"]
    sel_usable = st.selectbox("Filter by WES Usability", usable_opts)
with col3:
    decision_opts = ["All"] + sorted(df["decision"].dropna().unique().tolist())
    sel_decision = st.selectbox("Filter by Decision", decision_opts)

filtered = df.copy()
if sel_status != "All":
    filtered = filtered[filtered["pdf_status"] == sel_status]
if sel_usable == "WES Usable":
    filtered = filtered[filtered["usable_for_wes"] == True]
elif sel_usable == "Not Usable":
    filtered = filtered[filtered["usable_for_wes"] == False]
if sel_decision != "All":
    filtered = filtered[filtered["decision"] == sel_decision]

display_cols = [
    "code", "name", "hours", "grade", "pdf_status",
    "usable_for_wes", "possible_snhu_equivalent",
    "likely_snhu_area", "confidence", "decision", "notes"
]
display_cols = [c for c in display_cols if c in filtered.columns]

def color_row(row):
    if row.get("usable_for_wes") is True:
        return ["background-color: #d4edda"] * len(row)
    elif row.get("pdf_status") in ("Failed", "RN"):
        return ["background-color: #f8d7da"] * len(row)
    return [""] * len(row)

st.subheader(f"Estácio Courses ({len(filtered)} shown)")
st.dataframe(
    filtered[display_cols].rename(columns={
        "code": "Code", "name": "Course Name", "hours": "Hours",
        "grade": "Grade", "pdf_status": "Status",
        "usable_for_wes": "WES Usable",
        "possible_snhu_equivalent": "SNHU Equivalent",
        "likely_snhu_area": "SNHU Area",
        "confidence": "Confidence",
        "decision": "Decision", "notes": "Notes"
    }).style.apply(color_row, axis=1),
    use_container_width=True,
    hide_index=True,
)

# ── Summary stats ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 WES Summary")
usable = df[df["usable_for_wes"] == True]
not_usable = df[df["usable_for_wes"] == False]
potential_credits = usable["potential_snhu_credits"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Courses", len(df))
c2.metric("WES Usable", len(usable))
c3.metric("Not Usable (failed/NA)", len(not_usable))
c4.metric("Potential WES Credits", f"{int(potential_credits)}")

st.info(
    f"**{len(usable)} courses** are potentially usable for WES evaluation, "
    f"worth up to **{int(potential_credits)} credits** at SNHU (subject to WES course-by-course evaluation). "
    f"Final credit count depends on WES evaluation and SNHU transfer articulation."
)
