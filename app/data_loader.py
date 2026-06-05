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
