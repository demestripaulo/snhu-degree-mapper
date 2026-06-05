"""Broward College BAS Path — IT Cybersecurity & Ethical Hacking."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import broward_policies, broward_estacio_mapping, institution_cost_comparison

st.set_page_config(page_title="Broward College Path", page_icon="🐆", layout="wide")
st.title("🐆 Broward College — BAS in IT Cybersecurity")
st.markdown(
    "**BAS — Information Technology, Cybersecurity and Ethical Hacking (T300C AS)** — "
    "Rota alternativa via instituição local in-state, com máxima otimização de CPL, WES e CLEP."
)

bp = broward_policies()
em = broward_estacio_mapping()
cmp = institution_cost_comparison()

# ── Cost comparison banner ────────────────────────────────────────────────────
st.subheader("💰 Comparação de Custo: SNHU vs Broward College")

snhu = cmp["snhu"]
broward = cmp["broward"]
savings = cmp["savings_broward_vs_snhu"]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### 🟦 SNHU (online)")
    st.metric("Programa", snhu["program"])
    st.metric("$/crédito", f"${snhu['cost_per_credit']}")
    st.metric("Créditos restantes no SNHU", f"{snhu['credits_remaining']} cr")
    st.metric("Tuition no SNHU", f"${snhu['tuition_at_school']:,.0f}")
    st.metric("**Total estimado (SNHU)**", f"${snhu['total_estimate']:,.0f}")

with col2:
    st.markdown("#### 🟩 Broward College (in-state)")
    st.metric("Programa", broward["program"])
    st.metric("$/crédito", f"${broward['cost_per_credit']}")
    st.metric("Créditos obrigatórios no Broward", f"{broward['credits_at_broward']} cr")
    st.metric("Tuition no Broward (30 cr)", f"${broward['tuition_at_school']:,.0f}")
    st.metric("**Total estimado (Broward)**", f"${broward['total_estimate']:,.0f}")

with col3:
    st.markdown("#### 📊 Diferença")
    st.metric(
        "Economia escolhendo Broward",
        f"${savings:,.0f}",
        delta=f"-${savings:,.0f} vs SNHU",
        delta_color="normal"
    )
    st.info(
        f"**Broward custa ~${broward['cost_per_credit']/snhu['cost_per_credit']*100:.0f}%** "
        f"do preço por crédito do SNHU.\n\n"
        f"Com o mesmo cap de transferência (60 cr de entrada via WES), "
        f"o residual a pagar no Broward é "
        f"**${broward['tuition_at_school']:,.0f} vs ${snhu['tuition_at_school']:,.0f}** no SNHU."
    )

# ── Detailed cost breakdown ───────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Breakdown Detalhado de Custos")

items_snhu = [
    {"Item": "WES Course-by-Course Evaluation", "Phase": "Pré-matrícula", "SNHU ($)": 185, "Broward ($)": 185},
    {"Item": "Sophia Learning (~3 meses)",       "Phase": "Pré-matrícula", "SNHU ($)": 297, "Broward ($)": 297},
    {"Item": "CLEP American Government",         "Phase": "Pré-matrícula", "SNHU ($)": 93,  "Broward ($)": 93},
    {"Item": "CLEP Spanish Level 2",             "Phase": "Pré-matrícula", "SNHU ($)": 93,  "Broward ($)": 93},
    {"Item": "CCNA Renewal (se expirado)",        "Phase": "CPL prep",      "SNHU ($)": 0,   "Broward ($)": 330},
    {"Item": "PLA fees (~30 cr × $30)",           "Phase": "Broward only",  "SNHU ($)": 0,   "Broward ($)": 900},
    {"Item": "Tuition no SNHU (30 cr × $330)",   "Phase": "Graduação",     "SNHU ($)": snhu["tuition_at_school"], "Broward ($)": 0},
    {"Item": "Tuition no Broward (30 cr × $101.60)", "Phase": "Graduação", "SNHU ($)": 0,   "Broward ($)": broward["tuition_at_school"]},
]

df_cmp = pd.DataFrame(items_snhu)
total_snhu = df_cmp["SNHU ($)"].sum()
total_bc = df_cmp["Broward ($)"].sum()
totals = pd.DataFrame([{"Item": "**TOTAL**", "Phase": "—", "SNHU ($)": total_snhu, "Broward ($)": total_bc}])
df_display = pd.concat([df_cmp, totals], ignore_index=True)

def highlight_row(row):
    if row["Item"] == "**TOTAL**":
        return ["font-weight: bold; background-color: #e8f4f8"] * len(row)
    if row["Broward ($)"] == 0 and row["SNHU ($)"] > 0:
        return ["background-color: #fff3cd"] * len(row)
    if row["SNHU ($)"] == 0 and row["Broward ($)"] > 0:
        return ["background-color: #d4edda"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_display.style.apply(highlight_row, axis=1)
    .format({"SNHU ($)": "${:,.0f}", "Broward ($)": "${:,.0f}"}),
    use_container_width=True, hide_index=True,
)
st.caption("🟡 SNHU-only cost  |  🟢 Broward-only cost  |  Linhas brancas = comum aos dois caminhos")

# ── Estácio → Broward mapping ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("🗺️ Diploma Estácio → Eliminação de Disciplinas no Broward")

summ = em["summary"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cursos Estácio usáveis", summ["total_estacio_courses_usable"])
c2.metric("Disciplinas Broward potencialmente eliminadas", summ["broward_courses_potentially_eliminated"])
c3.metric("Créditos potencialmente eliminados", f"{summ['broward_credits_potentially_eliminated']} cr")
c4.metric("Valor dos créditos eliminados", f"${summ['broward_credits_potentially_eliminated'] * bp['cost_per_credit_usd']:,.0f}")

st.info(f"**Descoberta chave:** {summ['key_finding']}")
st.caption(f"⚠️ {summ['caveat']}")

# Mapping table
mappings = em["mappings"]
df_map = pd.DataFrame([{
    "Estácio": f"{m['estacio_code']} — {m['estacio_name']}",
    "Broward": f"{m['broward_code']} — {m['broward_title']}",
    "Créditos": m["broward_credits"],
    "Match": m["match_type"],
    "Confiança": m["confidence"],
    "Caminho de Eliminação": m["elimination_path"],
} for m in mappings])

conf_filter = st.multiselect(
    "Filtrar por Confiança",
    options=df_map["Confiança"].unique().tolist(),
    default=df_map["Confiança"].unique().tolist(),
)
filtered_map = df_map[df_map["Confiança"].isin(conf_filter)]

def color_match(row):
    if row["Match"] == "Strong":
        return ["background-color: #d4edda"] * len(row)
    elif row["Match"] == "Moderate":
        return ["background-color: #fff3cd"] * len(row)
    return ["background-color: #f8f9fa"] * len(row)

st.dataframe(filtered_map.style.apply(color_match, axis=1), use_container_width=True, hide_index=True)
st.caption(f"🟢 Strong match  |  🟡 Moderate  |  ⬜ Partial — {len(filtered_map)} mapeamentos mostrados")

# ── GE Coverage by Estácio ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📚 Cobertura de General Education pelo Estácio + Sophia + CLEP")

ge_data = em["ge_coverage_by_area"]
ge_rows = []
for area_key, area_val in ge_data.items():
    label = area_key.replace("_", " ").replace("area", "Área").title()
    ge_rows.append({
        "Área GE": label,
        "Cobertura pelo Estácio": area_val["covered_by_estacio"] if area_val["covered_by_estacio"] else "Não",
        "Caminho Recomendado": area_val["recommended_path"],
    })

df_ge = pd.DataFrame(ge_rows)

def color_ge(row):
    val = str(row["Cobertura pelo Estácio"])
    if val.lower().startswith("partial"):
        return ["background-color: #fff3cd"] * len(row)
    elif val.lower() == "false" or val.lower() == "não":
        return ["background-color: #f8d7da"] * len(row)
    return ["background-color: #d4edda"] * len(row)

st.dataframe(df_ge.style.apply(color_ge, axis=1), use_container_width=True, hide_index=True)

# ── Program requirements ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Estrutura do Programa BAS T300C AS")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Pré-requisitos (12 cr)")
    prereqs = bp["prerequisites"]
    df_pre = pd.DataFrame([{
        "Código": p["code"],
        "Disciplina": p["title"],
        "Créditos": p["credits"],
        "Caminho CPL": p["cpl_path"],
    } for p in prereqs])
    st.dataframe(df_pre.style.apply(lambda r: ["background-color: #d4edda"] * len(r), axis=1),
                 use_container_width=True, hide_index=True)

    st.markdown("#### Eletivas Disponíveis")
    df_elec = pd.DataFrame([{
        "Código": e["code"],
        "Disciplina": e["title"],
        "Créditos": e["credits"],
        "★": "Recomendado" if e.get("recommended") else "",
    } for e in bp["electives"]])
    st.dataframe(df_elec, use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### Core do Programa")
    df_core = pd.DataFrame([{
        "Código": c["code"],
        "Disciplina": c["title"],
        "Créditos": c["credits"],
        "CPL/Cert": c["cpl_path"] or "Cursar no Broward",
    } for c in bp["core_courses"]])

    def color_core(row):
        if row["CPL/Cert"] != "Cursar no Broward":
            return ["background-color: #d4edda"] * len(row)
        return [""] * len(row)

    st.dataframe(df_core.style.apply(color_core, axis=1), use_container_width=True, hide_index=True)

st.success(
    f"**Regras críticas do CPL:**\n\n"
    f"- **Residência mínima:** {bp['cpl_rules']['residency_min_credits']} cr DEVEM ser cursados no Broward\n"
    f"- **Janela de 3 anos para CTE:** Certs obtidas há mais de 3 anos → usar via PLA ($30/cr)\n"
    f"- **PLA aparece como 'CR'** — pode NÃO transferir para FAU/FIU\n"
    f"- **CLEP retroativo:** Exames feitos antes da matrícula são aceitos"
)

# ── Certification pipeline ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🏅 Pipeline de Certificações para o BAS")

cert_pipeline = [
    {"Certificação": "CompTIA Security+",      "Status": "Em andamento (Jul/2026)", "Cobre": "CTS2120C (pré-req, 4 cr)",   "Prioridade": "1 — Agora"},
    {"Certificação": "CCNA (renovação)",        "Status": "Verificar expiração",     "Cobre": "CTS1661C + CNT2111C + CNT2112C (12 cr)", "Prioridade": "2 — Jul/Ago 2026"},
    {"Certificação": "ISC2 SSCP",               "Status": "Planejar para 2027",      "Cobre": "CET2688C (4 cr)",            "Prioridade": "3"},
    {"Certificação": "CompTIA CySA+",           "Status": "Planejar para 2027",      "Cobre": "CIS3361C (3 cr)",            "Prioridade": "4"},
    {"Certificação": "CompTIA DataSys+",        "Status": "Planejar para 2027",      "Cobre": "ISM3212C (3 cr)",            "Prioridade": "5"},
    {"Certificação": "ISC2 CISSP",              "Status": "2027-2028",               "Cobre": "CTS3128C (4 cr) — mais valiosa", "Prioridade": "6"},
    {"Certificação": "Google PM Certificate",   "Status": "Ativa",                   "Cobre": "CIS1513C + ISM3314C (7 cr)", "Prioridade": "Já tem"},
    {"Certificação": "ISC2 CC",                 "Status": "Ativa",                   "Cobre": "Suporte ao portfólio CPL",   "Prioridade": "Já tem"},
]

df_cert = pd.DataFrame(cert_pipeline)

def color_cert(row):
    if row["Prioridade"] == "Já tem":
        return ["background-color: #d4edda"] * len(row)
    elif row["Prioridade"] == "1 — Agora":
        return ["background-color: #cce5ff"] * len(row)
    return [""] * len(row)

st.dataframe(df_cert.style.apply(color_cert, axis=1), use_container_width=True, hide_index=True)

# ── Pathway 2+2 FAU ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🎯 Alternativa: Pathway 2+2 → FAU")
p22 = bp["pathway_2plus2"]
st.info(
    f"**{p22['partner']}** — Articulação garantida por lei estadual da Flórida (Link2FAU)\n\n"
    f"**Programas disponíveis:**\n" +
    "\n".join(f"- {p}" for p in p22["program_options"]) +
    f"\n\n**Contato:** {p22['contact']}\n\n{p22['note']}"
)

# ── Open questions ────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("❓ Perguntas Abertas — Confirmar com Advisor do Broward"):
    for i, q in enumerate(bp["open_questions"], 1):
        st.markdown(f"{i}. {q}")

st.caption(
    "Dados baseados no documento de estratégia gerado em Jun/2026. "
    "Verificar valores atuais em broward.edu | Contato advisor: broward.edu/cpl"
)
