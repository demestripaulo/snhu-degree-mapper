#!/usr/bin/env python3
"""Extract SNHU Kuali CPL experiences and match them to selected BA/MS curricula."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE = "https://snhu.kuali.co/api/v1/catalog"
CATALOG_ID = "689dda35056c34c510a3a86b"
EXPERIENCE_CATALOG_ID = "62d0386e064ce7001cec61d1"
SELECTED_PROGRAMS = {
    "BA_IT": "EyjsXN8tl",
    "MS_CYBERSECURITY": "4112448tg",
    "MS_IT": "4kK2V4LYg",
}
TARGET_EXPERIENCE_PIDS = [
    "BJjHXqREbl",  # AWS Certified AI Practitioner
    "rk43YdsBv",  # CompTIA Security+
    "SkIwhDlRT",  # Google Cybersecurity Professional Certificate
    "Hk-HpfD2c",  # Google Project Management Professional Certificate
    "r14Eita4s",  # IBM Cybersecurity Analyst Professional Certificate
    "SJRBU_9Gyg",  # ISC2 Certified in Cybersecurity Exam
    "H13qiJIdw",  # Saylor BUS300
    "ry34Ezgo8",  # Saylor CS402
]


def get_json(path: str) -> dict | list:
    response = requests.get(f"{BASE}{path}", timeout=60)
    response.raise_for_status()
    return response.json()


def parse_course_links(html: str) -> list[dict]:
    soup = BeautifulSoup(html or "", "html.parser")
    courses = []
    for item in soup.select("li span"):
        text = " ".join(item.get_text(" ", strip=True).split())
        match = re.match(r"([A-Z]{2,5}\d{3}[A-Z]?|[A-Z]{2,5}\dELE|SNHU\d{3})\s+-\s+(.+?)\s+\(([^)]+)\)", text)
        if match:
            courses.append(
                {
                    "code": match.group(1),
                    "title": match.group(2),
                    "credits_text": match.group(3),
                }
            )
    return courses


def parse_total_credits(html: str) -> int | None:
    soup = BeautifulSoup(html or "", "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    match = re.search(r"Grand Total Credits:\s*(\d+)", text)
    return int(match.group(1)) if match else None


def fetch_programs() -> dict[str, dict]:
    programs = {}
    for key, pid in SELECTED_PROGRAMS.items():
        data = get_json(f"/program/{CATALOG_ID}/{pid}")
        rules = data.get("rulesRequirements", "")
        programs[key] = {
            "key": key,
            "pid": pid,
            "title": data.get("title"),
            "code": data.get("code"),
            "description": data.get("description"),
            "total_credits": parse_total_credits(rules),
            "courses": parse_course_links(rules),
            "specializations": [
                {"title": spec.get("title"), "pid": spec.get("pid")}
                for spec in data.get("specializations", [])
            ],
        }
    return programs


def parse_credit_awards(html: str) -> list[dict]:
    soup = BeautifulSoup(html or "", "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    pattern = re.compile(
        r"(\d+)\s+credit\(s\)\s+from the following:\s+"
        r"([A-Z]{2,5}\d{3}[A-Z]?|[A-Z]{2,5}\dELE|SNHU\d{3})\s+-\s+"
        r"(.+?)\s+\(([^)]+)\)"
    )
    return [
        {
            "credits_awarded": int(match.group(1)),
            "code": match.group(2),
            "title": match.group(3),
            "credits_text": match.group(4),
        }
        for match in pattern.finditer(text)
    ]


def fetch_experience_detail(item: dict) -> dict:
    detail = get_json(f"/experience/{EXPERIENCE_CATALOG_ID}/{item['pid']}")
    rules = detail.get("rulesAchievementCriteria", "")
    return {
        "vendor": item.get("groupFilter2", {}).get("name") or detail.get("groupFilter2", {}).get("name"),
        "category": detail.get("groupFilter1", {}).get("name"),
        "title": detail.get("title") or item.get("title"),
        "code": detail.get("code") or item.get("code"),
        "pid": item.get("pid"),
        "eligibility_timeframe": detail.get("eligibilityTimeframe"),
        "equivalent_courses": parse_course_links(rules),
        "credit_awards": parse_credit_awards(rules),
        "raw_url": f"https://www.snhu.edu/admission/transferring-credits/work-life-experience#/experiences/{item['pid']}",
    }


def fetch_experiences(vendors: set[str] | None, limit: int | None, sleep: float, include_targets: bool) -> list[dict]:
    summaries = get_json(f"/experiences/{EXPERIENCE_CATALOG_ID}?q=")
    if vendors:
        summaries = [
            item
            for item in summaries
            if item.get("groupFilter2", {}).get("name", "").lower() in vendors
        ]
    if include_targets:
        existing = {item["pid"] for item in summaries}
        all_summaries = get_json(f"/experiences/{EXPERIENCE_CATALOG_ID}?q=")
        summaries.extend(
            item for item in all_summaries
            if item["pid"] in TARGET_EXPERIENCE_PIDS and item["pid"] not in existing
        )
    if limit:
        summaries = summaries[:limit]

    rows = []
    for idx, item in enumerate(summaries, 1):
        rows.append(fetch_experience_detail(item))
        if sleep:
            time.sleep(sleep)
        if idx % 50 == 0:
            print(f"Fetched {idx}/{len(summaries)} CPL experiences...")
    return rows


def match_experiences(experiences: list[dict], programs: dict[str, dict]) -> list[dict]:
    required_codes = {
        key: {course["code"] for course in program["courses"]}
        for key, program in programs.items()
    }
    rows = []
    for exp in experiences:
        equivalents = exp.get("equivalent_courses", [])
        eq_codes = {course["code"] for course in equivalents}
        for program_key, codes in required_codes.items():
            exact = sorted(eq_codes & codes)
            is_graduate = program_key.startswith("MS_")
            elective = [
                course["code"]
                for course in equivalents
                if ("ELE" in course["code"] or "Elective" in course["title"])
                and (not is_graduate or is_graduate_level(course["code"]))
            ]
            if exact or elective:
                rows.append(
                    {
                        "program": program_key,
                        "vendor": exp["vendor"],
                        "experience": exp["title"],
                        "experience_code": exp["code"],
                        "eligibility_timeframe": exp["eligibility_timeframe"],
                        "match_type": "Exact curriculum course" if exact else "Elective bucket",
                        "matched_codes": exact or elective,
                        "equivalents": equivalents,
                        "decision": "Decide Later",
                        "course_status": "Not Started",
                        "url": exp["raw_url"],
                    }
                )
    return rows


def is_graduate_level(course_code: str) -> bool:
    match = re.search(r"(\d)", course_code)
    return bool(match and match.group(1) in {"5", "6", "7"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("outputs/snhu_cpl_matrix.json"))
    parser.add_argument("--vendors", nargs="*", help="Vendor names to include, case-insensitive exact match.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--no-targets", action="store_true", help="Do not force-include the curated target experiences.")
    args = parser.parse_args()

    vendors = {vendor.lower() for vendor in args.vendors} if args.vendors else None
    programs = fetch_programs()
    experiences = fetch_experiences(
        vendors=vendors,
        limit=args.limit,
        sleep=args.sleep,
        include_targets=not args.no_targets,
    )
    matches = match_experiences(experiences, programs)
    payload = {
        "source": {
            "catalog_id": CATALOG_ID,
            "experience_catalog_id": EXPERIENCE_CATALOG_ID,
            "work_life_url": "https://www.snhu.edu/admission/transferring-credits/work-life-experience#/home",
        },
        "programs": programs,
        "experiences": experiences,
        "matches": matches,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Programs: {len(programs)}")
    print(f"Experiences: {len(experiences)}")
    print(f"Curriculum/elective matches: {len(matches)}")
    print(args.out)


if __name__ == "__main__":
    main()
