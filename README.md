# Scriptly

An AI-powered blog content generation platform built with Flask and Google Gemini.

## Features

- **AI Blog Generation** - Generate complete blog posts from topics using Gemini
- **AI Humanizer** - Bypass AI detectors with section-based rewriting and 5-pass post-processing
- **Comment System** - Public comments with AI moderation (auto-approve, edit, or remove)
- **SEO Optimization** - Keyword analysis, readability scoring, meta tag generation
- **Public Blog Sites** - Each user gets a customizable public-facing blog
- **Semantic Search Agent** - Industry-standard agentic search with intent classification
- **Newsletter System** - Generate and send newsletters to subscribers
- **Team Collaboration** - Multi-user support with approval workflows
- **Forgot Password** - Secure password reset via Firebase email verification
- **Google Analytics** - Real-time analytics with Today/7 Days/30 Days period filters
- **Activity Log** - Paginated activity tracking for admin users
- **Schedule & Publish** - Schedule blogs for future publishing with AI-recommended times

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask, Python |
| Database | Firebase Firestore |
| Auth | Firebase Authentication (Email/Password, Google, Password Reset) |
| AI | Google Gemini (gemini-3-flash-preview) |
| Embeddings | Google gemini-embedding-001 |
| Email | Resend API |
| Deployment | Gunicorn, Docker, Railway |

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Taha-Khurram/Final_Year_Project.git
cd Final_Year_Project
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Firebase and Gemini credentials

# Run
python app.py
```

Access at `http://localhost:5000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_SERVICE_ACCOUNT` | Path to Firebase service account JSON | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `RESEND_API_KEY` | Resend API key for newsletters | No |
| `RAPIDAPI_KEY` | RapidAPI key for SEO tools | No |

## AI Agents

| Agent | Purpose |
|-------|---------|
| Blog Agent | Orchestrates full blog generation |
| Outline Agent | Creates structured outlines |
| Content Agent | Expands outlines to articles |
| SEO Agent | Optimizes content for search |
| Formatting Agent | Adds TOC, reading time, styling |
| Humanize Agent | Bypasses AI detectors with E-E-A-T rewriting |
| Comment Agent | AI moderation for public comments |
| Newsletter Agent | Generates newsletters from blogs |
| Semantic Search Agent | Industry-standard agentic search |

### Humanize Agent

Rewrites AI-generated content to bypass detectors (GPTZero, Originality.ai, ZeroGPT) using a multi-layered approach:

```
Content → Split into 2 chunks → Rewrite with rotating prompts → 5-pass post-processing → Validate
```

**Architecture:**
- **2-chunk rewriting** - Blog split at `##` headings, each half rewritten with a different prompt variant
- **4 prompt variants** - Direct, Conversational, Punchy, Relaxed — rotated to break statistical fingerprint uniformity
- **E-E-A-T rules** - Every prompt enforces Google's Experience, Expertise, Authoritativeness, Trustworthiness standards
- **5-pass post-processing** (no API cost):
  1. AI word replacement (35+ flagged words → human alternatives)
  2. Long sentence splitting (>20 words broken at conjunctions)
  3. Contraction mixing (realistic inconsistency)
  4. Paragraph length variation (merge short, split long)
  5. Imperfection injection (fillers, parentheticals)

### Comment Agent

AI-powered comment moderation using a single Gemini API call per comment:

- **Auto-approve** clean comments (published immediately)
- **Auto-edit** comments with grammar/formatting issues
- **Auto-remove** spam, toxic, or irrelevant comments (user never sees rejection)
- **Fail-open** design: if AI fails, comment is approved

### Semantic Search Agent

Implements industry-standard agentic patterns with minimal LLM usage:

```
Query → Understand → Plan → Execute Tools → Evaluate → Refine → Explain
```

**Features:**
- **Query Understanding** - Intent classification (informational/navigational/exploratory)
- **Query Expansion** - Synonym-based term expansion (no LLM cost)
- **Multi-Tool Execution** - Keyword, vector, and category search tools
- **Self-Evaluation** - Quality scoring with automatic refinement
- **Agent Insights** - Transparent reasoning displayed in UI

**Intent Classification:**
| Query Type | Example | Intent |
|------------|---------|--------|
| Questions | "how does react work?" | Informational |
| Content search | "python tutorial" | Navigational |
| Topic browse | "machine learning" | Exploratory |

## Public Site

Each user gets a public blog at `/site/<site_slug>` (or `/site/<user_id>` for backwards compatibility) with:
- **SEO-friendly URLs** - Custom site slugs instead of Firebase IDs
- Home, Blog, About, Contact pages
- **Legal Pages** - Privacy Policy, Terms of Service
- Newsletter subscription
- Semantic search with agent insights panel
- Category filtering
- Social sharing
- RSS feed, Sitemap, and robots.txt

## Documentation

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete documentation including:
- Detailed setup instructions
- API reference
- Configuration options
- Troubleshooting guide

## Project Structure

```
├── app/
│   ├── agents/           # AI agents
│   ├── firebase/         # Firebase services
│   ├── routes/           # API routes
│   ├── services/         # External services
│   ├── static/           # CSS, JS
│   ├── templates/        # HTML templates
│   └── utils/            # Utilities (date, slug, cache)
├── scripts/              # Utility scripts
├── docs/                 # Documentation
└── requirements.txt
```

## License

This project is part of a Final Year Project (FYP).

## Author

Taha Khurram - [GitHub](https://github.com/Taha-Khurram)
