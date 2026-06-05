#!/usr/bin/env python3
"""Parse the certified Estacio transcript and store WES/SNHU mapping inputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import duckdb
import pandas as pd
from pypdf import PdfReader


DEFAULT_PDF = Path("/Users/paulodemestri/Downloads/Histórico Escolar grad estacio_EN_certified.pdf")
DEFAULT_DB = Path("/Users/paulodemestri/Documents/SNHU/data/snhu_analytics.duckdb")
DEFAULT_OUT = Path("/Users/paulodemestri/Documents/GitHub/snhu-degree-mapper/outputs/estacio_wes_mapping.json")


RAW_RE = re.compile(
    r"(?P<term>20\d{2}\.\d)\s+-\s+Distance Learning\s+"
    r"(?P<type>[A-Z]\*?)\s+"
    r"(?P<code>[A-Z]{3}\d{4})\s+"
    r"(?P<name>.*?)\s+"
    r"(?P<hours>\d{2,3})\s+"
    r"(?P<grade>-|\d+\.\d)\s+"
    r"(?P<status>AP|IS|RN)\b",
    re.S,
)


AREA_RULES = [
    (("NETWORK",), "IT Major / IT Elective", "IT212 - Introduction to Computer Networks"),
    (("SECURITY", "AUDIT"), "IT Major / Cybersecurity Elective", "IT253/IT313/IT elective"),
    (("DATABASE", "BUSINESS INTELLIGENCE"), "IT Major / Data Elective", "IT/DAT database or analytics elective"),
    (("ALGORITHMS", "SOFTWARE DEVELOPMENT"), "IT Major / Programming Elective", "IT140 or IT elective"),
    (("OPERATING", "ORGANIZATION OF COMPUTERS"), "IT Major / Systems Elective", "IT202 or IT elective"),
    (("SYSTEM REQUIREMENTS", "SYSTEMS MODELING"), "IT Major / Systems Analysis", "IT304/IT337 or IT elective"),
    (("PROJECT MANAGEMENT",), "BA IT Major Choice / Management Elective", "QSO340/QSO345 or graduate QSO/IT elective"),
    (("GOVERNANCE", "SERVICE MANAGEMENT", "DELIVERY AND SUPPORT", "IMPLEMENTATION"), "IT Management Elective", "IT4ELE/IT management elective"),
    (("LAW", "ETHICS", "INTELLECTUAL PROPERTY"), "Ethics / Humanities / IT Elective", "IT659-like topic or humanities/free elective"),
    (("PSYCHOLOGY",), "Social Science / Free Elective", "Social science/free elective"),
    (("ADMINISTRATION", "MANAGEMENT", "SUPPLY CHAIN", "PURCHASES", "CONTRACT", "PROCESS"), "Business / Free Elective", "Business/free elective"),
    (("PORTUGUESE", "LIBRAS"), "Humanities / Free Elective", "Humanities/free elective"),
]


def clean_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"GPA of the Period:.*", "", value)
    return value.strip(" -")


def estimate_snhu_credits(hours: int) -> int:
    # SNHU equivalencies are commonly 3-credit buckets. WES/SNHU make the final conversion.
    return 3 if hours >= 44 else 0


def map_area(name: str) -> tuple[str, str, str]:
    upper = name.upper()
    for keywords, area, equivalent in AREA_RULES:
        if any(keyword in upper for keyword in keywords):
            confidence = "Medium" if area.startswith("IT") or "IT" in area else "Low"
            return area, equivalent, confidence
    return "Free Elective", "Free elective", "Low"


def parse_pdf(pdf_path: Path) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages[:4])
    rows = []
    for match in RAW_RE.finditer(text):
        row = match.groupdict()
        row["name"] = clean_name(row["name"])
        row["hours"] = int(row["hours"])
        row["grade"] = None if row["grade"] == "-" else float(row["grade"])
        row["pdf_status"] = {"AP": "Approved", "IS": "Exempt", "RN": "Failed"}[row["status"]]
        row["usable_for_wes"] = row["status"] in {"AP", "IS"}
        row["potential_snhu_credits"] = estimate_snhu_credits(row["hours"]) if row["usable_for_wes"] else 0
        area, equivalent, confidence = map_area(row["name"])
        row["likely_snhu_area"] = area
        row["possible_snhu_equivalent"] = equivalent
        row["confidence"] = "Low" if row["status"] == "IS" else confidence
        row["decision"] = "WES/SNHU Review" if row["usable_for_wes"] else "Not Usable"
        row["course_status"] = "Completed" if row["status"] == "AP" else ("WES Required" if row["status"] == "IS" else "Discarded")
        row["notes"] = (
            "Exempt subject on Estacio transcript; confirm whether WES lists awarded credit."
            if row["status"] == "IS"
            else "Passed course from certified English transcript."
            if row["status"] == "AP"
            else "Failed attempt; keep only for audit trail unless later passed."
        )
        rows.append(row)

    best_by_code = {}
    priority = {"AP": 3, "IS": 2, "RN": 1}
    for row in rows:
        current = best_by_code.get(row["code"])
        if current is None or priority[row["status"]] > priority[current["status"]] or row["term"] > current["term"]:
            best_by_code[row["code"]] = row

    deduped = []
    for row in rows:
        item = dict(row)
        item["dedupe_role"] = "Selected" if best_by_code[row["code"]] is row else "Duplicate/Lower outcome"
        if item["dedupe_role"] != "Selected":
            item["decision"] = "Discard Option"
            item["course_status"] = "Discarded"
            item["potential_snhu_credits"] = 0
        deduped.append(item)
    return deduped


def write_duckdb(db_path: Path, rows: list[dict]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS snhu_mapper")
    frame = pd.DataFrame(rows)
    con.register("estacio_rows", frame)
    con.execute("CREATE OR REPLACE TABLE snhu_mapper.estacio_wes_mapping AS SELECT * FROM estacio_rows")
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--duckdb", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = parse_pdf(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    write_duckdb(args.duckdb, rows)

    selected = [r for r in rows if r["dedupe_role"] == "Selected" and r["usable_for_wes"]]
    print(f"Parsed {len(rows)} transcript attempts; {len(selected)} selected WES-review candidates.")
    print(f"Potential SNHU credit buckets before official WES/SNHU review: {sum(r['potential_snhu_credits'] for r in selected)}")
    print(args.out)


if __name__ == "__main__":
    main()
