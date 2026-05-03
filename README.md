# Scriptly

An AI-powered blog content generation platform built with Flask and Google Gemini. Scriptly automates the full content creation lifecycle - from topic ideation to publication - with built-in humanization, SEO optimization, team collaboration, and public-facing blog sites.

---

## Features

### Content Generation & AI
- **AI Blog Generation** - Generate complete blog posts from topics using Google Gemini
- **AI Humanizer** - Bypass AI detectors (GPTZero, Originality.ai, ZeroGPT) with multi-chunk rewriting and 5-pass post-processing
- **SEO Optimization** - Keyword analysis, readability scoring, meta tag generation
- **AI Comment Moderation** - Auto-approve, auto-edit, or auto-remove comments in real-time
- **Semantic Search Agent** - Industry-standard agentic search with intent classification, query expansion, and vector similarity
- **Newsletter Generation** - AI-generated newsletters from published blog content
- **AI Publish Time Recommendations** - Optimal scheduling suggestions

### Platform Features
- **Public Blog Sites** - Each user gets a customizable public-facing blog with SEO-friendly URLs
- **Team Collaboration** - Multi-user support with role-based access control and approval workflows
- **User Management** - Invite users, assign roles (Admin/User), edit and delete users
- **Blog Scheduling** - Schedule posts for future publishing with background auto-publish
- **Google Analytics Integration** - Real-time analytics dashboard with configurable date periods
- **Activity Log** - Full audit trail of all admin actions (paginated)
- **Category Management** - Organize content with categories and filtering
- **Google Sheets Sync** - Export blog and user data to Google Sheets

### Security & Authentication
- **Firebase Authentication** - Email/Password, Google OAuth, Password Reset
- **Role-Based Access Control** - Admin and User roles with route protection
- **Session Management** - 15-minute inactivity timeout with HTTPOnly cookies
- **Admin Route Protection** - Unauthorized access returns 404 (not 403)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.x, Python 3.11 |
| Database | Firebase Firestore (NoSQL) |
| Authentication | Firebase Auth (Email/Password, Google OAuth, Password Reset) |
| AI / LLM | Google Gemini (gemini-2.0-flash) |
| Embeddings | Google gemini-embedding-001 (768 dimensions) |
| Email | Resend API |
| Analytics | Google Analytics Data API |
| SEO | RapidAPI Google Search |
| Sheets | Google Sheets API (gspread) |
| Deployment | Gunicorn, Docker, Railway, Nixpacks |
| Static Files | WhiteNoise, Flask-Compress (gzip) |
| Scheduling | APScheduler (background jobs) |

---

## Quick Start

### Prerequisites

- Python 3.9+
- Firebase project with Firestore and Authentication enabled
- Google Gemini API key

### Installation

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

### First-Time Setup

1. Navigate to `http://localhost:5000/signup`
2. Create your admin account (first user becomes admin)
3. Configure your public site in **Dashboard > Site Settings**
4. Start creating content!

---

## Environment Variables

Create a `.env` file in the project root:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key (32-byte hex) | Yes |
| `FIREBASE_SERVICE_ACCOUNT` | Path to Firebase service account JSON | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `FB_API_KEY` | Firebase client API key | Yes |
| `FB_AUTH_DOMAIN` | Firebase auth domain | Yes |
| `FB_PROJECT_ID` | Firebase project ID | Yes |
| `FB_STORAGE_BUCKET` | Firebase storage bucket | Yes |
| `FB_SENDER_ID` | Firebase messaging sender ID | Yes |
| `FB_APP_ID` | Firebase app ID | Yes |
| `RESEND_API_KEY` | Resend API key for newsletters | No |
| `FROM_EMAIL` | Newsletter sender email | No |
| `FROM_NAME` | Newsletter sender name | No |
| `RAPIDAPI_KEY` | RapidAPI key for SEO keyword research | No |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID (Analytics) | No |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret (Analytics) | No |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | Google Sheets spreadsheet ID | No |

---

## AI Agents

Scriptly uses a multi-agent architecture with 13 specialized AI agents:

| Agent | Purpose |
|-------|---------|
| **Blog Agent** | Orchestrates the full blog generation pipeline |
| **Outline Agent** | Creates structured blog outlines from topics |
| **Content Agent** | Expands outlines into complete articles |
| **SEO Agent** | Keyword analysis, readability scoring, meta generation |
| **Formatting Agent** | Adds TOC, reading time, heading structure |
| **Humanize Agent** | Bypasses AI detectors with E-E-A-T rewriting |
| **Comment Agent** | Real-time AI moderation for public comments |
| **Newsletter Agent** | Generates newsletters from published blogs |
| **Semantic Search Agent** | Agentic search with vector + keyword hybrid |
| **Category Agent** | Auto-categorization of blog content |
| **Approval Agent** | Content review workflow assistance |
| **Drafts Agent** | Draft management and suggestions |
| **Publish Time Agent** | AI-recommended optimal publish times |

### Humanize Agent Architecture

Rewrites AI-generated content to bypass detectors using a multi-layered approach:

```
Content → Split into 2 chunks at ## headings → Rewrite with rotating prompts → 5-pass post-processing → Validate
```

- **2-chunk rewriting** - Blog split at `##` headings, each half rewritten with a different prompt variant
- **4 prompt variants** - Direct, Conversational, Punchy, Relaxed (rotated to break statistical fingerprints)
- **E-E-A-T compliance** - Every prompt enforces Experience, Expertise, Authoritativeness, Trustworthiness
- **5-pass post-processing** (zero API cost):
  1. AI word replacement (35+ flagged words swapped to human alternatives)
  2. Long sentence splitting (>20 words broken at conjunctions)
  3. Contraction mixing (realistic inconsistency)
  4. Paragraph length variation (merge short, split long)
  5. Imperfection injection (fillers, parentheticals)

### Semantic Search Agent

Implements industry-standard agentic patterns:

```
Query → Understand → Plan → Execute Tools → Evaluate → Refine → Explain
```

- **Intent Classification** - Informational, Navigational, Exploratory (rule-based, no LLM cost)
- **Query Expansion** - Synonym-based term expansion (no LLM cost)
- **Multi-Tool Execution** - Keyword search, vector search, category search
- **Self-Evaluation** - Quality scoring with automatic refinement loop
- **Agent Insights** - Transparent reasoning displayed to users

### Comment Agent

Single Gemini API call per comment:
- **Auto-approve** clean comments (published immediately)
- **Auto-edit** comments with grammar/formatting issues
- **Auto-remove** spam, toxic, or irrelevant comments (user never sees rejection)
- **Fail-open design** - If AI fails, comment is approved as-is

---

## Public Blog Site

Each user gets a public blog at `/site/<site_slug>` with:

| Page | Description |
|------|-------------|
| Home | Landing page with featured posts |
| Blog | Paginated post listing with category filters |
| Post | Individual article with TOC, sharing, comments |
| About | Customizable about the author page |
| Contact | Contact form (stored in Firestore) |
| Privacy Policy | Configurable legal page |
| Terms of Service | Configurable legal page |
| RSS Feed | XML feed at `/feed.xml` |
| Sitemap | XML sitemap at `/sitemap.xml` |

**Site Features:**
- SEO-friendly custom slugs (backwards compatible with user IDs)
- Responsive design with mobile navigation
- Newsletter subscription forms
- Semantic search with agent insights panel
- Social sharing (Twitter, LinkedIn, Facebook)
- Category filtering
- Related post recommendations
- Performance: gzip, 7-day static cache, 2-minute query cache, instant.page prefetching

---

## Admin Dashboard

| Feature | Description |
|---------|-------------|
| **Content Creation** | AI-powered blog generation with real-time streaming |
| **Drafts** | Manage draft posts before publishing |
| **Approval Queue** | Review and approve/reject submitted blogs |
| **All Blogs** | Browse and filter all blogs across users |
| **Comment Moderation** | View, edit, restore, delete comments |
| **User Management** | Invite, edit roles, delete users |
| **Newsletter** | Generate and send newsletters to subscribers |
| **Analytics** | Google Analytics with Today/7 Days/30 Days filters |
| **SEO Tools** | Keyword research and content analysis |
| **Formatting Tools** | Content formatting and structure tools |
| **Schedule** | Blog scheduling with AI-recommended times |
| **Categories** | Manage content categories |
| **Activity Log** | Full audit trail of all actions |
| **Site Settings** | Configure public site appearance and SEO |
| **App Settings** | Application-wide configuration |

---

## Project Structure

```
FYP-main/
├── app/
│   ├── agents/                 # 13 AI agents
│   │   ├── blog_agent.py          # Pipeline orchestrator
│   │   ├── outline_agent.py       # Outline generation
│   │   ├── content_agent.py       # Content expansion
│   │   ├── seo_agent.py           # SEO optimization
│   │   ├── formatting_agent.py    # Formatting & TOC
│   │   ├── humanize_agent.py      # AI detector bypass
│   │   ├── comment_agent.py       # Comment moderation
│   │   ├── newsletter_agent.py    # Newsletter generation
│   │   ├── semantic_search_agent.py # Agentic search
│   │   ├── category_agent.py      # Auto-categorization
│   │   ├── approval_agent.py      # Review workflows
│   │   ├── drafts_agent.py        # Draft management
│   │   └── publish_time_agent.py  # Optimal publish times
│   ├── firebase/               # Firebase integration
│   │   ├── firebase_admin.py      # Admin SDK initialization
│   │   └── firestore_service.py   # Database operations
│   ├── routes/                 # API routes & blueprints
│   │   ├── auth.py                # Authentication
│   │   ├── blog_routes.py         # Blog CRUD & generation
│   │   ├── blogs_listing_routes.py # Blog filtering & listing
│   │   ├── user_mgmt.py           # User management
│   │   ├── site_routes.py         # Public blog site
│   │   ├── newsletter_routes.py   # Newsletter management
│   │   ├── analytics_routes.py    # Google Analytics
│   │   ├── settings_routes.py     # App & site settings
│   │   ├── activity_routes.py     # Activity log
│   │   └── schedule_routes.py     # Blog scheduling
│   ├── services/               # External service integrations
│   │   ├── email_service.py       # Resend API
│   │   ├── embedding_service.py   # Gemini embeddings
│   │   └── google_sheets_service.py # Google Sheets sync
│   ├── static/                 # Frontend assets
│   │   ├── css/                   # 26 stylesheets
│   │   ├── js/                    # 26 scripts
│   │   └── images/                # Image assets
│   ├── templates/              # 35 Jinja2 templates
│   │   ├── site/                  # Public site templates
│   │   ├── emails/                # Email templates
│   │   ├── errors/                # Error pages
│   │   └── partials/              # Reusable components
│   ├── utils/                  # Utility modules
│   │   ├── cache.py               # In-memory caching
│   │   ├── date_utils.py          # Timezone-aware formatting
│   │   ├── slug_utils.py          # URL slug generation
│   │   └── parallel.py            # Parallel execution
│   ├── __init__.py             # App factory
│   └── scheduler.py            # Background job scheduler
├── docs/
│   └── DOCUMENTATION.md        # Comprehensive documentation
├── app.py                      # Entry point
├── main.py                     # WSGI application wrapper
├── wsgi.py                     # WSGI entry point
├── config.py                   # Flask configuration
├── requirements.txt            # Python dependencies (19 packages)
├── Dockerfile                  # Docker containerization
├── Procfile                    # Heroku/Railway deployment
├── railway.json                # Railway configuration
├── nixpacks.toml               # Nixpacks configuration
├── firebase.json               # Firebase hosting config
├── .firebaserc                 # Firebase project config
└── .gitignore
```

---

## Deployment

### Local Development
```bash
python app.py
```

### Production (Gunicorn - Linux/Mac)
```bash
gunicorn main:app -w 4 -b 0.0.0.0:8080
```

### Production (Waitress - Windows)
```bash
waitress-serve --port=8080 main:app
```

### Docker
```bash
docker build -t scriptly .
docker run -p 8080:8080 scriptly
```

### Railway
Configured via `railway.json` and `Procfile`. Push to deploy.

---

## Database Schema

Firestore collections (created automatically):

| Collection | Description |
|-----------|-------------|
| `blogs` | Blog posts with content, metadata, embeddings, scheduling |
| `users` | User accounts with roles and team hierarchy |
| `categories` | Blog categories with post counts |
| `activities` | Admin activity audit trail |
| `comments` | Blog comments with moderation status |
| `site_settings` | Per-user public site configuration |
| `app_settings` | Global application settings |
| `newsletter_subscribers` | Email subscribers per site |
| `newsletter_history` | Sent newsletter records |
| `contact_submissions` | Contact form entries |

---

## Documentation

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete documentation including:
- Detailed setup instructions
- Full API reference with all endpoints
- Configuration options
- AI agent architecture details
- Public site customization
- Troubleshooting guide
- Production deployment guide

---

## License

This project is part of a Final Year Project (FYP) at the University.

## Author

**Taha Khurram** - [GitHub](https://github.com/Taha-Khurram)
