"""CPL Credits — Certifications and work/life experience credit mapping."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import cpl_credits_by_cert, target_certs, cpl_matrix

st.set_page_config(page_title="CPL Credits", page_icon="🏅", layout="wide")
st.title("🏅 CPL Credits — Certifications & Work/Life Experience")
st.markdown(
    "SNHU's **Credit for Prior Learning (CPL)** program awards credits for industry certifications. "
    "Credits are awarded based on active/current credentials reviewed by an SNHU advisor."
)

# ── Current cert portfolio ─────────────────────────────────────────────────────
st.subheader("📜 Your Certification Portfolio")
certs = cpl_credits_by_cert()
df_certs = pd.DataFrame(certs)

total_cpl = df_certs[df_certs["cpl_eligible"] == True]["credits"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Total CPL-Eligible Certs", df_certs[df_certs["cpl_eligible"] == True].shape[0])
c2.metric("Total CPL Credits", f"{total_cpl} cr")
c3.metric("SNHU Tuition Saved", f"${total_cpl * 330:,}")

def color_cert(row):
    if row["cpl_eligible"]:
        return ["background-color: #d4edda"] * len(row)
    return ["background-color: #f8f9fa"] * len(row)

st.dataframe(
    df_certs.rename(columns={
        "name": "Certification", "issuer": "Issuer",
        "cpl_eligible": "CPL Eligible", "credits": "Credits", "status": "Status"
    }).style.apply(color_cert, axis=1),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# ── Target certifications (from snhu_target_certifications.json) ───────────────
st.subheader("🎯 Target Certifications — Official SNHU CPL Awards")
tc = target_certs()
items = tc.get("items", [])
rows = []
for item in items:
    for award in item.get("awards", []):
        rows.append({
            "Certification": item["title"],
            "Vendor": item["vendor"],
            "Category": item["category"],
            "Eligibility": item.get("eligibility_timeframe") or "—",
            "SNHU Code": award.get("snhu_code", award.get("code", "")),
            "SNHU Course": award.get("snhu_course", award.get("title", "")),
            "Credits Awarded": award.get("credits_awarded"),
            "CPL URL": item["url"],
        })

df_target = pd.DataFrame(rows)
st.dataframe(df_target.drop(columns=["CPL URL"]), use_container_width=True, hide_index=True)

# ── CPL matrix matches for BA IT ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Full CPL Matrix — BA IT & MS Curriculum Matches")

try:
    matrix = cpl_matrix()
    matches = matrix.get("matches", [])
    if matches:
        df_matches = pd.DataFrame(matches)
        prog_filter = st.multiselect(
            "Filter by Program",
            options=df_matches["program"].unique().tolist(),
            default=["BA_IT"],
        )
        match_filter = st.multiselect(
            "Filter by Match Type",
            options=df_matches["match_type"].unique().tolist(),
            default=df_matches["match_type"].unique().tolist(),
        )
        filtered = df_matches[
            df_matches["program"].isin(prog_filter) &
            df_matches["match_type"].isin(match_filter)
        ]

        display_cols = ["program", "vendor", "experience", "match_type", "matched_codes", "eligibility_timeframe", "url"]
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[display_cols].rename(columns={
                "program": "Program", "vendor": "Vendor",
                "experience": "Experience/Cert", "match_type": "Match Type",
                "matched_codes": "Matched Codes", "eligibility_timeframe": "Eligibility",
                "url": "CPL URL"
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"{len(filtered)} matches shown (filtered from {len(df_matches)} total)")
    else:
        st.info("CPL matrix loaded but no matches found. Run `scripts/snhu_cpl_scraper.py` to refresh.")
except Exception as e:
    st.warning(f"Could not load full CPL matrix: {e}")

st.markdown("---")
st.info(
    "**Next step:** Contact SNHU transfer advisor at **transfer@snhu.edu** | 603.645.9687 "
    "with your full certification list for a preliminary CPL evaluation."
)
