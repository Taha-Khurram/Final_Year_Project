# Scriptly Documentation

Complete documentation for Scriptly - an AI-powered blog content generation platform.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Features](#features)
5. [AI Agents](#ai-agents)
6. [Public Site](#public-site)
7. [API Reference](#api-reference)
8. [Project Structure](#project-structure)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Scriptly is a full-stack blog platform that automates content creation using AI. It provides:

- **AI Content Generation**: Blog posts, outlines, and newsletters using Google Gemini
- **SEO Optimization**: Keyword analysis, readability scoring, meta tag generation
- **Public Blog Sites**: Each user gets a customizable public-facing blog
- **Semantic Search**: AI-powered search using embeddings and LLM reranking
- **Newsletter System**: Generate and send newsletters to subscribers
- **Team Collaboration**: Multi-user support with approval workflows

---

## Quick Start

### Prerequisites

- Python 3.9+
- Firebase project with Firestore
- Google Gemini API key

### Installation

```bash
# Clone repository
git clone https://github.com/Taha-Khurram/Final_Year_Project.git
cd Final_Year_Project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Run application
python app.py
```

Access at `http://localhost:5000`

### First-Time Setup

1. Open `http://localhost:5000/signup`
2. Create your account
3. Configure your public site in Dashboard > Site Settings
4. Start creating content!

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
FIREBASE_SERVICE_ACCOUNT=serviceAccountKey.json
GEMINI_API_KEY=your_gemini_api_key

# Firebase Client SDK (for frontend auth)
FB_API_KEY=your_firebase_api_key
FB_AUTH_DOMAIN=your-project.firebaseapp.com
FB_PROJECT_ID=your-project-id
FB_STORAGE_BUCKET=your-project.appspot.com
FB_SENDER_ID=your_sender_id
FB_APP_ID=your_app_id

# Optional - Newsletter emails
RESEND_API_KEY=re_xxxxxxxxxxxx
FROM_EMAIL=newsletter@yourdomain.com
FROM_NAME=Your Newsletter Name

# Optional - SEO keyword research
RAPIDAPI_KEY=your_rapidapi_key
```

### Firebase Setup

1. Create a project at [Firebase Console](https://console.firebase.google.com/)
2. Enable **Firestore Database**
3. Enable **Authentication** (Email/Password + Google)
4. Generate a service account key:
   - Project Settings > Service Accounts > Generate new private key
   - Save as `serviceAccountKey.json` in project root

### Firestore Collections

Created automatically:
- `blogs` - Blog posts and drafts
- `users` - User accounts
- `categories` - Blog categories
- `site_settings` - Public site configuration
- `newsletter_subscribers` - Email subscribers
- `newsletter_history` - Sent newsletters
- `contact_submissions` - Contact form entries
- `activities` - Activity log

---

## Features

### Content Generation

| Feature | Description |
|---------|-------------|
| **Topic to Blog** | Enter a topic, get a complete blog post |
| **Outline Generation** | AI creates structured outlines |
| **Content Expansion** | Expand outlines to full articles |
| **Formatting** | Auto-format with headings, TOC, reading time |

### SEO Tools

| Feature | Description |
|---------|-------------|
| **Keyword Analysis** | Research and optimize keywords |
| **Readability Score** | Flesch-Kincaid scoring |
| **Meta Generation** | Auto-generate meta descriptions |
| **Heading Structure** | Validate H1-H6 hierarchy |

### Newsletter System

| Feature | Description |
|---------|-------------|
| **AI Generation** | Create newsletters from published blogs |
| **Email Sending** | Send via Resend API |
| **Subscriber Management** | Track subscribers per site |
| **Draft Saving** | Save and edit drafts |
| **History** | View sent newsletters |

### Semantic Search Agent

Industry-standard agentic search implementation with minimal LLM usage.

| Feature | Description |
|---------|-------------|
| **Query Understanding** | Intent classification (informational/navigational/exploratory) |
| **Query Expansion** | Synonym-based term expansion without LLM |
| **Multi-Tool Search** | Keyword, vector, and category search tools |
| **Self-Evaluation** | Quality scoring with automatic refinement |
| **Agent Insights** | Transparent reasoning displayed in collapsible UI panel |
| **Embedding Search** | Google's gemini-embedding-001 for vector similarity |

**Agentic Loop:**
```
Query → Understand → Plan → Execute Tools → Evaluate → Refine → Explain
```

**Intent Types:**
| Intent | Detected When | Search Strategy |
|--------|---------------|-----------------|
| Informational | Questions (what, how, why?) | Semantic-heavy (50% vector) |
| Navigational | Keywords like "guide", "tutorial" | Keyword-heavy (60% keyword) |
| Exploratory | Topic browsing | Balanced (40/40/20) |

---

## AI Agents

### Blog Agent (`blog_agent.py`)
Orchestrates the full blog generation pipeline.

### Outline Agent (`outline_agent.py`)
Generates structured blog outlines from topics.

### Content Agent (`content_agent.py`)
Expands outlines into full blog posts.

### SEO Agent (`seo_agent.py`)
Analyzes and optimizes content for search engines.

### Formatting Agent (`formatting_agent.py`)
Formats content with TOC, reading time, and styling.

### Newsletter Agent (`newsletter_agent.py`)
Generates newsletter content from published blogs.

### Semantic Search Agent (`semantic_search_agent.py`)
Industry-standard agentic search with:
- **AgentState** dataclass for tracking reasoning
- **Rule-based intent classification** (no LLM cost)
- **Synonym expansion** via static dictionary
- **Tool execution**: keyword, vector, category tools
- **Quality evaluation** with automatic refinement
- **Insights API** returning agent reasoning to frontend

---

## Public Site

Each user gets a public blog at `/site/<site_identifier>` where `site_identifier` can be:
- **Site slug** (SEO-friendly): `/site/my-awesome-blog`
- **User ID** (backwards compatible): `/site/abc123xyz`

### Pages

| Page | URL | Description |
|------|-----|-------------|
| Home | `/site/<site_identifier>` | Landing page with featured posts |
| Blog | `/site/<site_identifier>/blog` | Paginated post listing |
| Post | `/site/<site_identifier>/post/<id>` | Single article view |
| About | `/site/<site_identifier>/about` | About the author |
| Contact | `/site/<site_identifier>/contact` | Contact form |
| Category | `/site/<site_identifier>/category/<name>` | Posts by category |
| Privacy | `/site/<site_identifier>/privacy-policy` | Privacy policy page |
| Terms | `/site/<site_identifier>/terms-of-service` | Terms of service page |
| RSS | `/site/<site_identifier>/rss.xml` | RSS feed |
| Sitemap | `/site/<site_identifier>/sitemap.xml` | XML sitemap |

### Site Settings

Customize via Dashboard > Site Settings:

| Setting | Description |
|---------|-------------|
| `site_slug` | SEO-friendly URL slug (e.g., `my-blog`) |
| `site_name` | Blog display name |
| `site_description` | Tagline/description |
| `logo_url` | Logo image URL |
| `primary_color` | Brand color (hex) |
| `posts_per_page` | Pagination size |
| `social_links` | Twitter, LinkedIn, GitHub |
| `contact_email` | Contact email address |
| `analytics_id` | Google Analytics ID |
| `timezone` | Display timezone (e.g., `America/New_York`) |
| `date_format` | Date display format |
| `privacy_policy` | Privacy policy content |
| `terms_of_service` | Terms of service content |

### Features

- **Responsive Design**: Mobile-first with hamburger menu
- **Newsletter Signup**: Forms throughout the site
- **Contact Form**: Stored in Firestore
- **Social Sharing**: Twitter, LinkedIn, Facebook
- **Table of Contents**: Auto-generated from headings
- **Related Posts**: Same-category recommendations
- **Semantic Search**: Floating button with agent insights panel

### Performance

- **Compression**: Gzip via Flask-Compress
- **Static Caching**: 7-day cache via WhiteNoise
- **Query Caching**: 2-minute in-memory cache
- **Prefetching**: instant.page for fast navigation

---

## API Reference

### Blog Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Generate blog from topic |
| GET | `/api/get_blog/<id>` | Get blog by ID |
| POST | `/api/update_status/<id>` | Change blog status |
| DELETE | `/api/delete_blog/<id>` | Delete blog |

### SEO Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/seo/analyze` | Analyze content |
| POST | `/api/seo/keywords` | Research keywords |

### Newsletter

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/newsletter/generate` | Generate from blogs |
| POST | `/api/newsletter/send` | Send to subscribers |
| GET | `/api/newsletter/subscribers` | List subscribers |
| GET | `/api/newsletter/history` | Sent newsletters |

### Public Site

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/site/<site_identifier>` | Home page |
| GET | `/site/<site_identifier>/blog` | Blog listing |
| GET | `/site/<site_identifier>/post/<id>` | Single post |
| GET | `/site/<site_identifier>/about` | About page |
| GET | `/site/<site_identifier>/contact` | Contact page |
| POST | `/site/<site_identifier>/subscribe` | Newsletter signup |
| POST | `/site/<site_identifier>/contact` | Contact form |
| POST | `/site/<site_identifier>/semantic-search` | AI search |
| GET | `/site/<site_identifier>/rss.xml` | RSS feed |
| GET | `/site/<site_identifier>/sitemap.xml` | XML sitemap |
| GET | `/site/<site_identifier>/robots.txt` | Robots file |
| GET | `/site/<site_identifier>/privacy-policy` | Privacy policy |
| GET | `/site/<site_identifier>/terms-of-service` | Terms of service |

> **Note:** `site_identifier` can be either a custom site slug (e.g., `my-blog`) or the user's Firebase ID for backwards compatibility.

---

## Project Structure

```
FYP-main/
├── app/
│   ├── agents/                 # AI agents
│   │   ├── blog_agent.py
│   │   ├── content_agent.py
│   │   ├── formatting_agent.py
│   │   ├── newsletter_agent.py
│   │   ├── outline_agent.py
│   │   ├── semantic_search_agent.py
│   │   └── seo_agent.py
│   ├── firebase/               # Firebase services
│   │   ├── firebase_admin.py
│   │   └── firestore_service.py
│   ├── routes/                 # API routes
│   │   ├── auth.py
│   │   ├── blog_routes.py
│   │   ├── newsletter_routes.py
│   │   ├── settings_routes.py
│   │   ├── site_routes.py
│   │   └── user_mgmt.py
│   ├── services/               # External services
│   │   ├── email_service.py
│   │   └── embedding_service.py
│   ├── static/                 # Static assets
│   │   ├── css/
│   │   └── js/
│   ├── templates/              # HTML templates
│   │   ├── site/              # Public site
│   │   ├── emails/            # Email templates
│   │   └── partials/          # Reusable components
│   └── utils/                  # Utilities
│       ├── cache.py
│       ├── date_utils.py       # Timezone-aware date formatting
│       ├── parallel.py
│       └── slug_utils.py       # URL slug generation
├── scripts/
│   └── backfill_embeddings.py  # Generate embeddings for existing blogs
├── docs/
│   └── DOCUMENTATION.md        # This file
├── config.py                   # App configuration
├── app.py                      # Entry point
├── wsgi.py                     # WSGI entry
└── requirements.txt            # Dependencies
```

---

## Troubleshooting

### Firebase Connection Issues
- Verify `serviceAccountKey.json` path in `.env`
- Check Firestore rules allow read/write
- Ensure Firebase Admin SDK is initialized

### Gemini API Errors
- Verify API key is valid and not leaked
- Check quota limits in Google Cloud Console
- For "model not found" errors, check model name

### Email Not Sending
- Verify Resend API key
- Check domain verification status
- Review Resend dashboard for errors

### Semantic Search Not Working
- Run `python scripts/backfill_embeddings.py` to generate embeddings
- Check Gemini API key is valid
- Verify blogs have `embedding` field in Firestore

### Performance Issues
- Check in-memory cache is working
- Verify static file caching headers
- Monitor Firestore query counts

---

## Production Deployment

### Using Gunicorn (Linux/Mac)
```bash
gunicorn wsgi:app -w 4 -b 0.0.0.0:8000
```

### Using Waitress (Windows)
```bash
waitress-serve --port=8000 wsgi:app
```

### Docker
```bash
docker build -t scriptly .
docker run -p 8000:8000 scriptly
```

### Railway
Configured via `railway.json` and `Dockerfile`.

---

## Support

For issues, open a ticket at [GitHub Issues](https://github.com/Taha-Khurram/Final_Year_Project/issues).

---

*Last Updated: April 2026*
