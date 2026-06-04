# SNHU Degree Mapper

Analyzes SNHU degree programs against a student's qualifications — certifications, prior education, and transfer credits — and generates a personalized roadmap to the fastest and most cost-effective degree path.

## What it does

- Maps all transferable credits (CPL certifications, WES-evaluated foreign degrees, Sophia Learning)
- Fetches live SNHU program pages for up-to-date curriculum data
- Uses the Claude API to score each program's fit and calculate time/cost to completion
- Outputs a full markdown report with ranked recommendations and an action checklist

## Output

Running the script produces `snhu_degree_report.md` with:

- Credit portfolio summary (capped at SNHU's 90-credit transfer max)
- Per-program analysis: fit score, remaining credits, estimated months, total cost
- Strategic ranking and optimal degree sequence
- Sophia Learning gen-ed plan with ROI breakdown
- Immediate action checklist

## Setup

```bash
pip install anthropic httpx beautifulsoup4
export ANTHROPIC_API_KEY=your_key_here
python snhu_degree_mapper.py
```

## Student profile

The profile in `snhu_degree_mapper.py` is pre-configured for Paulo Demestri:

- 20+ years IT, cybersecurity, and operations experience
- Certifications: CCNA, ISC2 CC, CompTIA A+/Security+, MCSA, Google PM, PMI
- Education: Estácio de Sá (IT Management, Brazil) + PUC Minas AI/ML postgrad (in progress)
- Location: Boca Raton, FL — trilingual (English, Portuguese, Spanish)

To adapt for a different student, update the `PAULO_PROFILE` dict at the top of the script.

## Programs analyzed

| Level | Program |
|-------|---------|
| Bachelor's | BA in Information Technologies |
| Bachelor's | BS in Information Technologies |
| Bachelor's | BS in Cybersecurity |
| Bachelor's | BS in Business Administration (IT Management) |
| Master's | MBA Online |
| Master's | MS in Computer Science (AI concentration) |
| Master's | MS in Cybersecurity |

## Recommended path (for this profile)

```
Sophia Learning (3 months, $297) + WES evaluation
        ↓
BA in IT or BS Cybersecurity — 30 credits at SNHU (~10–12 months, ~$10K)
        ↓
MS in Cybersecurity — 36 credits (~12–14 months, ~$23K)
```

Total: ~26 months and ~$33K to MS level, versus $120K–$200K for a traditional 4-year degree.
