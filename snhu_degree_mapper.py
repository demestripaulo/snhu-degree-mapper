#!/usr/bin/env python3
"""
SNHU Degree Mapper — Chat Branding Project
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fetches SNHU program curricula, maps against Paulo's qualifications,
and identifies the fastest path to bachelor's or master's degree.

Usage:
    python snhu_degree_mapper.py

Requirements:
    pip install anthropic httpx beautifulsoup4 markdownify

Output:
    snhu_degree_report.md — Full analysis and roadmap
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import httpx
    from bs4 import BeautifulSoup
    import anthropic
except ImportError:
    print("Installing required packages...")
    os.system("pip install anthropic httpx beautifulsoup4 --quiet")
    import httpx
    from bs4 import BeautifulSoup
    import anthropic

# ──────────────────────────────────────────────────────────────────────────────
# PAULO'S PROFILE
# ──────────────────────────────────────────────────────────────────────────────

PAULO_PROFILE = {
    "name": "Paulo Demestri",
    "location": "Boca Raton, FL",
    "languages": ["English (Full Professional)", "Portuguese (Native)", "Spanish (Native/Bilingual)"],

    "education": [
        {
            "title": "Postgraduate Specialization — Artificial Intelligence & Machine Learning",
            "institution": "PUC Minas (Pontifical Catholic University of Minas Gerais)",
            "country": "Brazil",
            "status": "In Progress (2025–2027)",
            "us_equivalent": "Postgraduate Certificate (WES pending)",
            "credits_potential": 15
        },
        {
            "title": "Technology Associate's Degree — Information Technology Management",
            "institution": "Universidade Estácio de Sá",
            "country": "Brazil",
            "status": "Completed (2015–2017)",
            "us_equivalent": "Associate's Degree (WES pending)",
            "credits_potential": 60
        }
    ],

    "certifications": [
        {"name": "ISC2 CC (Certified in Cybersecurity)",         "issuer": "ISC2",     "snhu_cpl": True,  "credits_est": 6},
        {"name": "CCNA (Cisco Certified Network Associate)",     "issuer": "Cisco",    "snhu_cpl": True,  "credits_est": 9},
        {"name": "HCNA (Huawei Certified Network Associate)",   "issuer": "Huawei",   "snhu_cpl": False, "credits_est": 0},
        {"name": "MCSA (Microsoft Certified Solutions Associate)","issuer": "Microsoft","snhu_cpl": True,  "credits_est": 6},
        {"name": "MCTS (Microsoft Certified Technology Specialist)","issuer": "Microsoft","snhu_cpl": True,"credits_est": 3},
        {"name": "CompTIA A+",                                   "issuer": "CompTIA",  "snhu_cpl": True,  "credits_est": 6},
        {"name": "CompTIA Security+ (In Progress)",              "issuer": "CompTIA",  "snhu_cpl": True,  "credits_est": 6},
        {"name": "FCNSA (Fortinet Certified Network Security)",  "issuer": "Fortinet", "snhu_cpl": False, "credits_est": 0},
        {"name": "Google Project Management Certificate",        "issuer": "Google",   "snhu_cpl": True,  "credits_est": 3},
        {"name": "Google AI Essentials",                         "issuer": "Google",   "snhu_cpl": True,  "credits_est": 3},
        {"name": "PMI PM Fast-track",                            "issuer": "PMI",      "snhu_cpl": True,  "credits_est": 3},
        {"name": "Six Sigma White Belt",                         "issuer": "Various",  "snhu_cpl": False, "credits_est": 0},
        {"name": "Advanced IP Routing, Switching & Troubleshooting (Cisco)", "issuer": "Cisco", "snhu_cpl": True, "credits_est": 3},
    ],

    "experience": [
        {
            "title": "Account Manager",
            "company": "Hawk-Eye Protective Services",
            "duration": "2024–Present",
            "highlights": [
                "Portfolio: $2.5M annual revenue, 10 high-value client accounts",
                "Team: 90+ employees",
                "Training program coordination",
                "Client relationship management and escalation resolution"
            ]
        },
        {
            "title": "Area Supervisor",
            "company": "Hawk-Eye Protective Services",
            "duration": "2021–2023",
            "highlights": ["Multi-site management", "Technology consulting for client sites"]
        },
        {
            "title": "IT Consultant (Self-Employed)",
            "company": "Independent",
            "duration": "2019–2024",
            "highlights": [
                "Network design and implementation for SMBs",
                "Router, proxy, switch, WAN, DNS/DHCP configuration"
            ]
        },
        {
            "title": "IT Consultant",
            "company": "Concessionária Porto Novo S.A.",
            "duration": "2016–2019",
            "highlights": [
                "Full IT infrastructure implementation",
                "Cisco, HP, Fortinet, Extreme Networks configuration",
                "IT budget management"
            ]
        }
    ],

    "core_skills": [
        "Network Architecture & Configuration (CCNA-level)",
        "Cybersecurity & Information Assurance",
        "Windows Server Administration (MCSA)",
        "IT Infrastructure & Systems Integration",
        "Operations Management",
        "Account & Client Management",
        "Team Leadership & Coaching (90+ employees)",
        "Project Management (PMBOK/ITIL)",
        "Budget Oversight",
        "AI/ML Fundamentals (in progress)",
        "Virtualization",
        "Process Improvement",
        "Trilingual Business Communication"
    ],

    "total_years_experience": 20,
    "wes_evaluation_pending": True
}

# ──────────────────────────────────────────────────────────────────────────────
# SNHU PROGRAMS TO ANALYZE
# ──────────────────────────────────────────────────────────────────────────────

SNHU_PROGRAMS = [
    {
        "level": "Bachelor's",
        "name": "BA in Information Technologies",
        "url": "https://www.snhu.edu/admission/academic-catalogs#/programs/EyjsXN8tl",
        "total_credits": 120,
        "max_transfer": 90,
        "notes": "Selected bachelor's path. Most transfer-friendly IT option with 21 free elective credits.",
        "relevant_to": ["IT operations", "networking", "systems", "tech leadership"]
    },
    {
        "level": "Master's",
        "name": "MS in Cybersecurity",
        "url": "https://www.snhu.edu/admission/academic-catalogs#/programs/4112448tg",
        "total_credits": 36,
        "max_transfer": 12,
        "notes": "Graduate target option. Undergraduate BA credits satisfy the bachelor's credential but do not directly reduce graduate credits; SNHU may accept up to 12 graduate transfer credits.",
        "relevant_to": ["cybersecurity", "information security", "security management"]
    },
    {
        "level": "Master's",
        "name": "MS in Information Technology (Information Technology concentration)",
        "url": "https://www.snhu.edu/admission/academic-catalogs#/programs/4kK2V4LYg/V1gvpS4qg",
        "total_credits": 36,
        "max_transfer": 12,
        "notes": "Graduate target option. Requires completed bachelor's first; undergraduate Sophia/WES credits are for BA completion, not graduate-course reduction.",
        "relevant_to": ["IT management", "systems", "technical leadership", "enterprise technology"]
    }
]

# ──────────────────────────────────────────────────────────────────────────────
# SOPHIA LEARNING GEN ED COURSES (for credit gap filling)
# ──────────────────────────────────────────────────────────────────────────────

SOPHIA_COURSES = [
    {"course": "English Composition I",          "credits": 3, "months": 1},
    {"course": "English Composition II",         "credits": 3, "months": 1},
    {"course": "Introduction to Statistics",     "credits": 3, "months": 1},
    {"course": "Introduction to Philosophy",     "credits": 3, "months": 1},
    {"course": "US History",                     "credits": 3, "months": 1},
    {"course": "Macroeconomics",                 "credits": 3, "months": 1},
    {"course": "Microeconomics",                 "credits": 3, "months": 1},
    {"course": "Introduction to Psychology",     "credits": 3, "months": 1},
    {"course": "Business Communication",         "credits": 3, "months": 1},
    {"course": "Project Management",             "credits": 3, "months": 1},
]

# ──────────────────────────────────────────────────────────────────────────────
# WEB FETCHER
# ──────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_page(url: str, retries: int = 3) -> str | None:
    """Fetch a webpage with retry logic."""
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                response = client.get(url, headers=HEADERS)
                if response.status_code == 200:
                    return response.text
                print(f"  ⚠ HTTP {response.status_code} for {url}")
        except Exception as e:
            print(f"  ⚠ Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(2)
    return None

def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove navigation, scripts, styles
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Clean up excessive whitespace
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

# ──────────────────────────────────────────────────────────────────────────────
# CREDIT ESTIMATOR
# ──────────────────────────────────────────────────────────────────────────────

def calculate_credit_estimate(profile: dict) -> dict:
    """Calculate estimated transferable credits from all sources."""

    cert_credits = sum(
        c["credits_est"] for c in profile["certifications"]
        if c["snhu_cpl"]
    )

    edu_credits = sum(e["credits_potential"] for e in profile["education"])

    sophia_credits = sum(c["credits"] for c in SOPHIA_COURSES)

    total_potential = cert_credits + edu_credits + sophia_credits
    # Cap at SNHU's 90-credit maximum
    total_capped = min(total_potential, 90)

    # Sophia cost estimate
    sophia_months = max(2, len(SOPHIA_COURSES) // 3)  # ~3 courses/month
    sophia_cost = sophia_months * 99

    return {
        "certifications": cert_credits,
        "education": edu_credits,
        "sophia_gen_ed": sophia_credits,
        "total_potential": total_potential,
        "total_capped_at_snhu_max": total_capped,
        "remaining_at_snhu": 120 - total_capped,
        "sophia_months": sophia_months,
        "sophia_cost_usd": sophia_cost,
        "snhu_credits_at_330_per": (120 - total_capped) * 330,
        "cpl_eligible_certs": [
            c["name"] for c in profile["certifications"] if c["snhu_cpl"]
        ]
    }

# ──────────────────────────────────────────────────────────────────────────────
# CLAUDE API ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────

def analyze_program_fit(
    client: anthropic.Anthropic,
    program: dict,
    profile: dict,
    page_content: str,
    credit_estimate: dict
) -> dict:
    """Use Claude to deeply analyze program fit and fastest path."""

    prompt = f"""You are an academic advisor specializing in credit transfer and accelerated degree completion.

STUDENT PROFILE:
{json.dumps(profile, indent=2)}

PROGRAM BEING ANALYZED:
{json.dumps(program, indent=2)}

CREDIT ESTIMATE:
{json.dumps(credit_estimate, indent=2)}

PROGRAM PAGE CONTENT (partial):
{page_content[:3000] if page_content else "Page content unavailable - use known SNHU curriculum structure."}

SNHU CPL POLICY:
- Accepts up to 90 transfer credits (75% of 120-credit bachelor's)
- Recognized partners: Cisco, CompTIA, ISC2, Microsoft, Google, PMI
- Accepts Sophia Learning, StraighterLine, Study.com courses
- Credit for prior learning (CPL) through portfolio assessment also available
- Associate's degree (WES evaluated) can count toward general education requirements

Analyze this specific program for Paulo and provide:

1. OVERALL FIT SCORE (1-10) with reasoning
2. ESTIMATED CREDITS ALREADY COVERED based on his certifications, education, and Sophia plan
3. REMAINING CREDITS he would need to complete at SNHU
4. ESTIMATED TIME to completion (months) assuming 2 courses/term, 8-week terms
5. ESTIMATED COST breakdown
6. TOP 3 ADVANTAGES of this program for his profile
7. TOP 2 CHALLENGES or gaps
8. FASTEST PATH — specific action sequence to maximize credit transfer

Be specific, data-driven, and practical. Focus on Paulo's multilingual, IT+Security+Leadership profile.

Respond in valid JSON with these exact keys:
fit_score, estimated_covered_credits, remaining_credits, time_months,
total_cost_usd, advantages, challenges, fastest_path_steps, recommendation_summary"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON parse error for {program['name']}: {e}")
        return {"error": str(e), "raw": raw}
    except Exception as e:
        print(f"  ⚠ API error for {program['name']}: {e}")
        return {"error": str(e)}

def generate_ranking(
    client: anthropic.Anthropic,
    analyses: list,
    profile: dict
) -> str:
    """Generate final ranked comparison and overall recommendation."""

    prompt = f"""You are a senior academic and career strategist.

STUDENT: {profile['name']} — Tech Humanist Leader
- 20+ years IT + Security + Operations experience
- Managing $2.5M portfolio, 90+ employees
- Trilingual: English, Spanish, Portuguese
- Goal: Fastest path to a US degree that maximizes career leverage for C-suite/leadership roles
- Secondary goal: Path to Master's in AI/ML or Business

PROGRAM ANALYSES:
{json.dumps(analyses, indent=2)}

Based on all analyses, provide:

1. RANKED LIST of programs (1 = best fit) with one-line rationale each
2. OVERALL WINNER — which single program gives Paulo the best ROI of time + money + career impact
3. THE OPTIMAL SEQUENCE — e.g., "Start with X → then Y → then Z"
4. IMMEDIATE NEXT 5 ACTIONS Paulo should take this week/month
5. KEY RISK to watch out for

Write this as a clear, direct executive summary. Use markdown formatting.
Be decisive — Paulo needs a clear recommendation, not a list of options."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating ranking: {e}"

# ──────────────────────────────────────────────────────────────────────────────
# REPORT GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

def generate_report(
    profile: dict,
    credit_estimate: dict,
    program_analyses: list,
    ranking_summary: str
) -> str:
    """Assemble the full markdown report."""

    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")

    md = f"""# SNHU Degree Mapper — {profile['name']}
### Generated: {timestamp} | Chat Branding Project

---

## 1. Credit Portfolio Summary

| Source | Estimated Credits |
|--------|-------------------|
| Certifications (CPL) | {credit_estimate['certifications']} |
| Education (WES evaluated) | {credit_estimate['education']} |
| Sophia Learning (gen ed plan) | {credit_estimate['sophia_gen_ed']} |
| **Total Potential** | **{credit_estimate['total_potential']}** |
| **SNHU Cap (90 max)** | **{credit_estimate['total_capped_at_snhu_max']}** |
| **Remaining at SNHU** | **{credit_estimate['remaining_at_snhu']}** |

**CPL-Eligible Certifications:**
{chr(10).join(f"- ✅ {c}" for c in credit_estimate['cpl_eligible_certs'])}

**Sophia Learning Plan:** ~{credit_estimate['sophia_months']} months × $99/mo = **${credit_estimate['sophia_cost_usd']}**

---

## 2. Program Analyses

"""

    for item in program_analyses:
        prog = item["program"]
        analysis = item["analysis"]

        md += f"### {prog['level']}: {prog['name']}\n"
        md += f"**URL:** {prog['url']}\n\n"

        if "error" in analysis:
            md += f"> ⚠️ Analysis error: {analysis['error']}\n\n"
            continue

        fit = analysis.get("fit_score", "N/A")
        stars = "⭐" * int(fit) if isinstance(fit, (int, float)) else "N/A"

        md += f"| Metric | Value |\n|--------|-------|\n"
        md += f"| Fit Score | {fit}/10 {stars} |\n"
        md += f"| Credits Already Covered | ~{analysis.get('estimated_covered_credits', 'N/A')} |\n"
        md += f"| Remaining Credits at SNHU | ~{analysis.get('remaining_credits', 'N/A')} |\n"
        md += f"| Estimated Time | ~{analysis.get('time_months', 'N/A')} months |\n"
        md += f"| Total Cost Estimate | ${analysis.get('total_cost_usd', 'N/A'):,} |\n\n"

        if "advantages" in analysis:
            md += "**Advantages:**\n"
            for adv in analysis["advantages"]:
                md += f"- ✅ {adv}\n"
            md += "\n"

        if "challenges" in analysis:
            md += "**Challenges:**\n"
            for ch in analysis["challenges"]:
                md += f"- ⚠️ {ch}\n"
            md += "\n"

        if "fastest_path_steps" in analysis:
            md += "**Fastest Path:**\n"
            steps = analysis["fastest_path_steps"]
            if isinstance(steps, list):
                for i, step in enumerate(steps, 1):
                    md += f"{i}. {step}\n"
            else:
                md += f"{steps}\n"
            md += "\n"

        if "recommendation_summary" in analysis:
            md += f"**Summary:** {analysis['recommendation_summary']}\n\n"

        md += "---\n\n"

    md += f"""## 3. Strategic Ranking & Recommendation

{ranking_summary}

---

## 4. Sophia Learning Gen Ed Plan

| Course | Credits | Est. Time |
|--------|---------|-----------|
"""
    for course in SOPHIA_COURSES:
        md += f"| {course['course']} | {course['credits']} | ~{course['months']} month |\n"

    sophia_total_credits = sum(c["credits"] for c in SOPHIA_COURSES)
    sophia_total_months = max(2, len(SOPHIA_COURSES) // 3)
    md += f"| **TOTAL** | **{sophia_total_credits}** | **~{sophia_total_months} months** |\n"

    md += f"""
**Cost:** ~{sophia_total_months} months × $99 = **${sophia_total_months * 99}**
**ROI vs SNHU tuition:** {sophia_total_credits} credits × $330/credit = **${sophia_total_credits * 330:,} saved**

---

## 5. Immediate Action Checklist

- [ ] Request WES evaluation at wes.org (~$160-200, takes 4-7 business days)
- [ ] Start Sophia Learning subscription ($99/month) — sophia.org
- [ ] Contact SNHU transfer advisor: transfer@snhu.edu | 603.645.9687
- [ ] Request preliminary CPL credit evaluation with list of certifications
- [ ] Complete Security+ (in progress) — adds ~6 CPL credits immediately
- [ ] Verify current WGU vs SNHU articulation for your specific program
- [ ] Complete Google AI Essentials if not already done — 3 CPL credits

---
*Report generated by SNHU Degree Mapper | Chat Branding Project*
*For personal use only. Verify all credit transfer policies directly with SNHU.*
"""
    return md

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  SNHU DEGREE MAPPER — Chat Branding Project")
    print("=" * 60)
    print(f"  Student: {PAULO_PROFILE['name']}")
    print(f"  Programs to analyze: {len(SNHU_PROGRAMS)}")
    print("=" * 60)

    # Initialize Anthropic client
    client = anthropic.Anthropic()

    # Step 1: Calculate credit estimate
    print("\n📊 Calculating credit portfolio...")
    credit_estimate = calculate_credit_estimate(PAULO_PROFILE)
    print(f"  ✅ Potential transferable credits: {credit_estimate['total_potential']}")
    print(f"  ✅ After SNHU cap: {credit_estimate['total_capped_at_snhu_max']}")
    print(f"  ✅ Remaining at SNHU: {credit_estimate['remaining_at_snhu']}")

    # Step 2: Fetch and analyze each program
    print("\n🌐 Fetching program pages and running analysis...")
    program_analyses = []

    for program in SNHU_PROGRAMS:
        print(f"\n  → {program['name']}")

        # Fetch page
        html = fetch_page(program["url"])
        page_text = extract_text_from_html(html) if html else ""

        if html:
            print(f"    ✅ Page fetched ({len(page_text)} chars)")
        else:
            print(f"    ⚠ Using cached knowledge (page unavailable)")

        # Analyze with Claude
        print(f"    🤖 Analyzing with Claude...")
        analysis = analyze_program_fit(client, program, PAULO_PROFILE, page_text, credit_estimate)

        if "error" not in analysis:
            score = analysis.get("fit_score", "?")
            remaining = analysis.get("remaining_credits", "?")
            months = analysis.get("time_months", "?")
            print(f"    ✅ Fit: {score}/10 | Remaining: {remaining} credits | Time: {months} months")
        else:
            print(f"    ⚠ Analysis issue: {analysis.get('error', 'unknown')[:60]}")

        program_analyses.append({"program": program, "analysis": analysis})
        time.sleep(1)  # Rate limiting

    # Step 3: Generate overall ranking
    print("\n🏆 Generating strategic ranking and recommendation...")
    ranking_summary = generate_ranking(client, program_analyses, PAULO_PROFILE)
    print("  ✅ Ranking complete")

    # Step 4: Assemble and save report
    print("\n📝 Assembling report...")
    report = generate_report(PAULO_PROFILE, credit_estimate, program_analyses, ranking_summary)

    output_path = Path("snhu_degree_report.md")
    output_path.write_text(report, encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  ✅ REPORT SAVED: {output_path.resolve()}")
    print(f"  📊 Programs analyzed: {len(SNHU_PROGRAMS)}")
    print(f"  💳 Est. credits already covered: {credit_estimate['total_capped_at_snhu_max']}/90")
    print(f"  📚 Remaining at SNHU: {credit_estimate['remaining_at_snhu']} credits")
    print(f"{'=' * 60}")

    # Print quick summary to terminal
    print("\n📋 QUICK SUMMARY:")
    for item in program_analyses:
        p = item["program"]
        a = item["analysis"]
        if "fit_score" in a:
            print(f"  {a['fit_score']:>4}/10  {p['level']:12} — {p['name']}")

if __name__ == "__main__":
    main()
