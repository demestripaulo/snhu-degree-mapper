"""Shared data loading utilities for the SNHU Degree Mapper BI app."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUTS = ROOT / "outputs"
DATA = ROOT / "data"


@lru_cache(maxsize=None)
def load_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def profile() -> dict:
    return load_json(ROOT / "extracted_data.json")["PAULO_PROFILE"]


def wes_mapping() -> list[dict]:
    return load_json(OUTPUTS / "estacio_wes_mapping.json")


def cpl_matrix() -> dict:
    return load_json(OUTPUTS / "snhu_cpl_matrix_relevant.json")


def target_certs() -> dict:
    return load_json(OUTPUTS / "snhu_target_certifications.json")


def ba_it_curriculum() -> list[dict]:
    data = load_json(OUTPUTS / "snhu_cpl_matrix_relevant_sample.json")
    return data["programs"]["BA_IT"]["courses"]


def ms_cyb_curriculum() -> list[dict]:
    data = load_json(OUTPUTS / "snhu_cpl_matrix_relevant_sample.json")
    return data["programs"]["MS_CYBERSECURITY"]["courses"]


def ms_it_curriculum() -> list[dict]:
    data = load_json(OUTPUTS / "snhu_cpl_matrix_relevant_sample.json")
    return data["programs"]["MS_IT"]["courses"]


def bs_it_curriculum() -> list[dict]:
    pol = policies()
    return pol["bs_it_cybersecurity"]["core_courses"] + pol["bs_it_cybersecurity"]["cybersecurity_concentration"]


def wes_analysis() -> dict:
    return policies()["wes_vs_gened_analysis"]


def broward_policies() -> dict:
    return load_json(DATA / "broward_policies.json")


def broward_estacio_mapping() -> dict:
    return load_json(DATA / "broward_estacio_mapping.json")


def broward_as_programs() -> dict:
    return load_json(DATA / "broward_as_programs.json")


def institution_cost_comparison() -> dict:
    """Side-by-side cost comparison: SNHU vs Broward for Paulo's profile."""
    cs = credit_summary()
    broward = broward_policies()

    snhu_remaining = cs["remaining_at_snhu"]
    snhu_cost_per_cr = cs["snhu_cost_per_credit"]

    # Broward scenario
    # Entry: WES Tecnólogo = AS entry (60 cr) → BAS needs 60 more
    # CPL/CTE from certs covers ~30 cr of the 60 BAS credits
    # Residency minimum: 30 cr at Broward
    broward_cr_per = broward["cost_per_credit_usd"]

    snhu_total_remaining = snhu_remaining * snhu_cost_per_cr

    return {
        "snhu": {
            "institution": "SNHU (online)",
            "program": "BA in Information Technologies",
            "credits_remaining": snhu_remaining,
            "cost_per_credit": snhu_cost_per_cr,
            "pre_enrollment": 185 + 297,    # WES + Sophia (3 mo)
            "clep_total": 186,              # 2 CLEP exams
            "tuition_at_school": snhu_total_remaining,
            "total_estimate": snhu_total_remaining + 185 + 297 + 186,
        },
        "broward": {
            "institution": "Broward College (in-state)",
            "program": "BAS — IT Cybersecurity and Ethical Hacking",
            "credits_at_broward": 30,       # residency minimum
            "cost_per_credit": broward_cr_per,
            "pre_enrollment": 185 + 297,    # WES + Sophia (3 mo)
            "clep_total": 186,              # CLEP Gov + CLEP Spanish
            "pla_fees": 900,                # ~30 cr PLA @ $30/cr
            "ccna_renewal": 330,            # if expired
            "tuition_at_school": 30 * broward_cr_per,
            "total_estimate": (30 * broward_cr_per) + 185 + 297 + 186 + 900 + 330,
        },
        "savings_broward_vs_snhu": snhu_total_remaining - (30 * broward_cr_per + 900 + 330),
    }


def sophia_mapping() -> dict:
    return load_json(DATA / "sophia_ba_it_mapping.json")


def policies() -> dict:
    return load_json(DATA / "snhu_policies.json")


# ── Credit aggregations ────────────────────────────────────────────────────────

def credit_summary() -> dict:
    prof = profile()

    cert_credits = sum(
        c["credits_est"] for c in prof["certifications"] if c["snhu_cpl"]
    )

    edu_credits = sum(e["credits_potential"] for e in prof["education"])

    sophia = sophia_mapping()
    sophia_credits = sophia["summary"]["total_credits"]

    total_potential = cert_credits + edu_credits + sophia_credits
    cap = 90
    capped = min(total_potential, cap)

    return {
        "certifications": cert_credits,
        "education_wes": edu_credits,
        "sophia": sophia_credits,
        "total_potential": total_potential,
        "capped_at_90": capped,
        "remaining_at_snhu": 120 - capped,
        "ba_it_total": 120,
        "snhu_cost_per_credit": 330,
        "cost_remaining": (120 - capped) * 330,
    }


def cpl_credits_by_cert() -> list[dict]:
    prof = profile()
    rows = []
    for c in prof["certifications"]:
        rows.append({
            "name": c["name"],
            "issuer": c["issuer"],
            "cpl_eligible": c["snhu_cpl"],
            "credits": c["credits_est"],
            "status": "Eligible" if c["snhu_cpl"] else "Not eligible",
        })
    return rows


def wes_approved_courses() -> list[dict]:
    return [
        c for c in wes_mapping()
        if c.get("status") in ("AP",) or c.get("pdf_status") == "Approved"
    ]


def ba_it_coverage() -> list[dict]:
    """Return BA IT courses annotated with coverage source."""
    curriculum = ba_it_curriculum()
    wes = {c.get("possible_snhu_equivalent", "").split()[0] for c in wes_mapping() if c.get("usable_for_wes")}
    certs = target_certs().get("items", [])
    cert_codes = {award["snhu_code"] for c in certs for award in c.get("awards", [])}
    sophia = {c["snhu_code"] for c in sophia_mapping()["courses"]}

    rows = []
    for course in curriculum:
        code = course["code"]
        if code in cert_codes:
            source = "CPL — Certification"
            covered = True
        elif code in sophia:
            source = "Sophia Learning"
            covered = True
        elif any(code in w for w in wes):
            source = "WES Transfer"
            covered = True
        else:
            source = "Take at SNHU"
            covered = False
        rows.append({
            "code": code,
            "title": course["title"],
            "credits": 3,
            "covered": covered,
            "source": source,
            "status": "Covered" if covered else "Needed",
        })
    return rows
