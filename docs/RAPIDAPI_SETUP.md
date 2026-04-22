# SEO Keyword Research Setup

## API: Google Search (RapidAPI)

**URL:** https://rapidapi.com/herosAPI/api/google-search74

### What It Provides:
- Related keywords from Google search
- "People also search for" suggestions
- Real Google search data

---

## Setup

### 1. Add to `.env`:
```env
RAPIDAPI_KEY=2059f520a3msh6174fb9e35a612dp1eaf92jsnceac30d22253
```

### 2. That's it!

The SEO Agent is pre-configured to use this API.

---

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│                     SEO KEYWORD RESEARCH                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Your Blog: "AI in Healthcare"                                 │
│  Region: Pakistan (PK)                                         │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 1: Extract seed keywords with Gemini AI            │   │
│  │         → "AI healthcare", "medical AI", "health tech"  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                   │
│                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 2: Google Search API finds related keywords        │   │
│  │                                                          │   │
│  │   Query: "AI healthcare pakistan"                        │   │
│  │                                                          │   │
│  │   Related Keywords Found:                                │   │
│  │   • "ai healthcare solutions in pakistan"                │   │
│  │   • "medical ai startups lahore"                         │   │
│  │   • "how to use ai in healthcare"                        │   │
│  │   • "ai diagnosis tools pakistan"                        │   │
│  │   • "chatgpt for doctors pakistan"                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                   │
│                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 3: Calculate difficulty for each keyword           │   │
│  │                                                          │   │
│  │   Keyword                          Difficulty   Rank     │   │
│  │   ─────────────────────────────────────────────────      │   │
│  │   "AI healthcare" (2 words)        75  HIGH     Hard     │   │
│  │   "ai healthcare pakistan"         35  MEDIUM   OK       │   │
│  │   "ai diagnosis tools pakistan"    20  LOW      EASY ✓   │   │
│  │   "chatgpt for doctors pakistan"   15  LOW      EASY ✓   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                   │
│                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 4: Select best keywords (low competition + volume) │   │
│  │                                                          │   │
│  │   PRIMARY: "ai diagnosis tools pakistan"                 │   │
│  │   SECONDARY: "chatgpt for doctors pakistan",             │   │
│  │              "medical ai startups lahore"                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                   │
│                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 5: Auto-optimize blog content                      │   │
│  │                                                          │   │
│  │   BEFORE: "Benefits of AI in Healthcare"                 │   │
│  │   AFTER:  "AI Diagnosis Tools in Pakistan: Transform     │   │
│  │            Your Healthcare Practice in 2025"             │   │
│  │                                                          │   │
│  │   ✓ Keyword in title                                     │   │
│  │   ✓ Keyword in first 100 words                          │   │
│  │   ✓ Keywords in H2 headings                             │   │
│  │   ✓ Meta description with keyword                        │   │
│  │   ✓ FAQ section added                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Difficulty Scoring

The agent calculates difficulty based on:

| Factor | Effect |
|--------|--------|
| Single word ("AI") | +25 (harder) |
| 2 words | 0 (baseline) |
| 3 words | -15 (easier) |
| 4 words | -25 (easier) |
| 5+ words | -30 (easiest) |
| Contains location ("pakistan", "lahore") | -20 (easier) |
| Question word ("how", "what") | -10 (easier) |
| Contains year ("2025") | -5 (easier) |
| Generic terms ("best", "top") | +10 (harder) |

### Example:
```
Keyword: "how to use ai in healthcare pakistan"

Base difficulty:           50
- 7 words:                -30
- Contains "pakistan":    -20
- Contains "how":         -10
─────────────────────────────
Final difficulty:          -10 → 5 (minimum)

Result: VERY EASY to rank!
```

---

## Usage

```python
from app.agents.seo_agent import SEOAgent

agent = SEOAgent()

result = agent.optimize_blog(
    title="Benefits of AI in Healthcare",
    content="Artificial intelligence is transforming...",
    region="PK"
)

# Primary keyword (lowest competition)
print(result['keyword_research']['primary_keyword'])
# {
#   'keyword': 'ai diagnosis tools pakistan',
#   'difficulty_score': 20,
#   'competition': 'LOW',
#   'search_volume': 300
# }

# Optimized title
print(result['optimized']['optimized_title'])
# "AI Diagnosis Tools in Pakistan: Healthcare Revolution 2025"

# SEO Score
print(result['optimized']['seo_score'])
# 85
```

---

## API Limits

| Plan | Requests/Month | Cost |
|------|---------------|------|
| Free | 500 | $0 |
| Basic | 10,000 | $10 |
| Pro | 100,000 | $50 |

500 free requests is plenty for your FYP!

---

## Fallback Options

If the API fails, the agent automatically falls back to:

1. **PyTrends** (Google Trends) - FREE, no key needed
2. **AI Estimation** - Gemini estimates based on keyword patterns

This ensures the system **always works**!
