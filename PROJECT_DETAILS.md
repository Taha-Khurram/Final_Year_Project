# Scriptly - Project Details

**Final Year Project (FYP)**  
**Author:** Taha Khurram  
**Repository:** [github.com/Taha-Khurram/Final_Year_Project](https://github.com/Taha-Khurram/Final_Year_Project)

---

## 1. Project Overview

Scriptly is an AI-powered blog content generation and management platform. It automates the entire blog creation workflow from topic input to SEO-optimized, publication-ready content. The platform features a multi-agent AI architecture powered by Google Gemini, Firebase backend, and a public-facing blog site for each user.

### Key Highlights

- **AI-Powered Content Generation**: Automated outline and full blog generation using Google Gemini
- **Multi-Agent Architecture**: Specialized AI agents for different tasks (outline, content, SEO, formatting)
- **Admin Approval Workflow**: Human-in-the-loop review before publishing
- **Public Blog Sites**: Each user gets a shareable public blog site
- **SEO Optimization**: Built-in SEO analysis with keyword research and readability scoring
- **Professional Formatting**: Markdown to HTML conversion with TOC, reading time, and statistics

---

## 2. Features

### 2.1 Core Features (Implemented)

| Feature | Description |
|---------|-------------|
| **AI Blog Generation** | Generate complete blog posts from a simple topic/prompt |
| **User Authentication** | Firebase Auth with Google sign-in support |
| **Draft Management** | Save, edit, preview, and manage blog drafts |
| **Approval Queue** | Admin review workflow for content moderation |
| **Category Management** | Organize blogs with custom categories |
| **User Management** | Admin controls for managing platform users |
| **Dashboard** | Real-time stats, recent activity, and quick actions |

### 2.2 Advanced Features (Implemented)

| Feature | Description |
|---------|-------------|
| **SEO Agent** | Keyword analysis, meta descriptions, readability scores (Flesch-Kincaid), heading structure validation |
| **Formatting Agent** | Markdown to HTML conversion, TOC generation, reading time calculation, professional styling |
| **Public Blog Site** | Each user gets a public site at `/site/{user_id}` with customizable settings |
| **Site Settings** | Configure site name, description, and niche |
| **Real-time SEO Tools** | Live content analysis with keyword density and optimization suggestions |

### 2.3 Planned Features (Future)

- AI Best-Time Publishing
- Semantic Search with vector embeddings
- AI-Generated Newsletter
- Smart Comment Moderation
- WhatsApp Integration

---

## 3. Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Flask** | Python web framework |
| **Firebase Firestore** | NoSQL document database |
| **Firebase Auth** | User authentication |
| **Google Gemini AI** | Content generation (gemini-3-flash-preview) |
| **Gunicorn / Waitress** | Production WSGI servers |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Jinja2 Templates** | Server-side rendering |
| **Bootstrap 5** | UI components and responsive design |
| **Bootstrap Icons** | Icon library |
| **Custom CSS/JS** | Styling and interactivity |

### Utilities
| Technology | Purpose |
|------------|---------|
| **WhiteNoise** | Static file serving |
| **Markdown** | Content formatting |
| **PyTrends** | Google Trends integration |
| **RapidAPI** | SEO keyword research APIs |

---

## 4. Architecture

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Application Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ blog_routes │  │ auth_routes │  │ site_routes │  │user_mgmt│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AI Agents Layer                           │
│  ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐ │
│  │ BlogAgent│ │Outline  │ │ Content  │ │  SEO   │ │Formatting │ │
│  │(Pipeline)│ │ Agent   │ │  Agent   │ │ Agent  │ │   Agent   │ │
│  └──────────┘ └─────────┘ └──────────┘ └────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   Google    │ │  Firebase   │ │  RapidAPI   │
            │   Gemini    │ │  Firestore  │ │  (SEO APIs) │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### 4.2 AI Pipeline Flow

```
User Input (Topic/Keywords)
        │
        ▼
┌───────────────────┐
│   Outline Agent   │  → Generate structured blog outline
└───────────────────┘
        │
        ▼
┌───────────────────┐
│   Content Agent   │  → Expand outline to full markdown content
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Formatting Agent  │  → Convert to HTML, generate TOC, calculate reading time
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    SEO Agent      │  → Analyze keywords, readability, meta description (optional)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Category Agent   │  → Auto-suggest category based on content
└───────────────────┘
        │
        ▼
    [Draft Created]
        │
        ▼
┌───────────────────┐
│  Admin Approval   │  → Human review before publishing
└───────────────────┘
        │
        ▼
    [Published Blog]
        │
        ▼
┌───────────────────┐
│   Public Site     │  → Accessible at /site/{user_id}
└───────────────────┘
```

---

## 5. Project Structure

```
FYP-main/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── agents/                  # AI agents
│   │   ├── blog_agent.py        # Main pipeline orchestrator
│   │   ├── outline_agent.py     # Blog outline generation
│   │   ├── content_agent.py     # Full content generation
│   │   ├── seo_agent.py         # SEO analysis & optimization
│   │   ├── formatting_agent.py  # Markdown → HTML formatting
│   │   ├── category_agent.py    # Category suggestion
│   │   ├── approval_agent.py    # Approval workflow
│   │   └── drafts_agent.py      # Draft management
│   ├── firebase/                # Firebase integration
│   │   ├── firebase_admin.py    # Firebase initialization
│   │   └── firestore_service.py # Database operations
│   ├── routes/                  # API & page routes
│   │   ├── blog_routes.py       # Blog CRUD, SEO, formatting APIs
│   │   ├── auth.py              # Authentication routes
│   │   ├── site_routes.py       # Public blog site routes
│   │   └── user_mgmt.py         # User management (admin)
│   ├── static/                  # CSS, JS, images
│   │   ├── css/
│   │   └── js/
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── partials/            # Reusable components (sidebar)
│   │   └── site/                # Public blog site templates
│   └── utils/                   # Utility modules
│       ├── cache.py             # Caching utilities
│       └── parallel.py          # Parallel execution helpers
├── docs/                        # Documentation
│   └── RAPIDAPI_SETUP.md        # SEO API setup guide
├── config.py                    # App configuration
├── app.py                       # Entry point
├── wsgi.py                      # WSGI entry point
├── requirements.txt             # Python dependencies
├── README.md                    # Project overview
├── ADVANCED_FEATURES.md         # Feature implementation plan
└── PROJECT_DETAILS.md           # This document
```

---

## 6. Database Schema (Firestore)

### 6.1 Collections

#### `blogs`
```javascript
{
  id: string,                    // Auto-generated document ID
  title: string,                 // Blog title
  content: {
    markdown: string,            // Original markdown
    html: string,                // Formatted HTML
    body: string,                // Plain text
    toc: array,                  // Table of contents
    toc_html: string,            // TOC as HTML
    reading_time: string,        // "5 min read"
    statistics: {
      word_count: number,
      paragraph_count: number,
      heading_count: number
    }
  },
  outline: array,                // Blog structure
  status: "DRAFT" | "UNDER_REVIEW" | "PUBLISHED",
  category: string,              // Category name
  author_id: string,             // User ID
  author: string,                // Display name
  seo: {
    enabled: boolean,
    seo_score: number,
    meta_description: string,
    keywords: array
  },
  created_at: timestamp,
  updated_at: timestamp
}
```

#### `users`
```javascript
{
  id: string,                    // Firebase Auth UID
  email: string,
  displayName: string,
  role: "USER" | "ADMIN",
  created_at: timestamp,
  last_login: timestamp
}
```

#### `categories`
```javascript
{
  id: string,
  name: string,
  user_id: string,               // Owner (user-specific categories)
  blog_count: number,
  created_at: timestamp
}
```

#### `site_settings`
```javascript
{
  user_id: string,               // Primary key
  site_name: string,
  site_description: string,
  niche: string,
  updated_at: timestamp
}
```

#### `activity_log`
```javascript
{
  id: string,
  user_id: string,
  user_name: string,
  type: "generated" | "edited" | "published" | "deleted" | "status_change",
  action_text: string,
  blog_title: string,
  created_at: timestamp
}
```

---

## 7. API Endpoints

### 7.1 Blog Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Dashboard page |
| GET | `/create` | Blog creation page |
| GET | `/drafts` | Drafts list page |
| GET | `/approval` | Approval queue page |
| GET | `/categories` | Categories page |
| POST | `/api/generate` | Generate blog from prompt |
| GET | `/api/get_blog/<id>` | Get blog by ID |
| POST | `/api/update_blog/<id>` | Update blog content |
| POST | `/api/update_status/<id>` | Change blog status |
| DELETE | `/api/delete_blog/<id>` | Delete blog |
| POST | `/api/unpublish/<id>` | Unpublish blog |

### 7.2 Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/categories` | Create category |
| POST | `/api/edit_category/<id>` | Rename category |
| DELETE | `/api/delete_category/<id>` | Delete category |

### 7.3 SEO Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/seo-tools` | SEO tools page |
| POST | `/api/seo/analyze` | Analyze content for SEO |
| POST | `/api/seo/keywords` | Research keywords for topic |
| POST | `/api/seo/optimize-blog/<id>` | Optimize existing blog |
| GET | `/api/seo/drafts` | Get drafts for SEO |
| POST | `/api/seo/analyze-draft/<id>` | Analyze draft SEO |

### 7.4 Formatting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/formatting-tools` | Formatting tools page |
| POST | `/api/format` | Format markdown to HTML |

### 7.5 Site Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/site-settings` | Site settings page |
| POST | `/api/site-settings` | Update site settings |

### 7.6 Public Site (No Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/site/<user_id>` | Public blog homepage |
| GET | `/site/<user_id>/post/<blog_id>` | Single blog post |
| GET | `/site/<user_id>/about` | About page |
| GET | `/site/<user_id>/category/<name>` | Filter by category |

### 7.7 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Authenticate user |
| GET | `/signup` | Signup page |
| POST | `/signup` | Register user |
| GET | `/logout` | Logout user |

---

## 8. User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **USER** | Create blogs, manage own drafts, submit for approval, view own published content |
| **ADMIN** | All USER permissions + approve/reject blogs, publish content, manage all users, access user management |

### Workflow by Role

**Regular User:**
1. Creates blog → Status: DRAFT
2. Submits for review → Status: UNDER_REVIEW
3. Awaits admin approval

**Admin:**
1. Creates blog → Can directly publish (PUBLISHED)
2. Reviews pending blogs in approval queue
3. Approves (PUBLISHED) or rejects (back to DRAFT)

---

## 9. Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_SERVICE_ACCOUNT` | Path to Firebase service account JSON | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `SECRET_KEY` | Flask session secret key | Yes |
| `RAPIDAPI_KEY` | RapidAPI key for SEO tools | Optional |

---

## 10. Setup & Installation

### Prerequisites
- Python 3.9+
- Firebase project with Firestore enabled
- Google Cloud project with Gemini API enabled

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/Taha-Khurram/Final_Year_Project.git
cd Final_Year_Project

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Add Firebase service account
# Place serviceAccountKey.json in project root

# 6. Run application
python app.py
# Or for production:
gunicorn wsgi:app
```

---

## 11. Development Timeline

| Milestone | Status | Description |
|-----------|--------|-------------|
| Initial Setup | Complete | Flask app, Firebase integration, basic structure |
| Authentication | Complete | Firebase Auth with Google sign-in |
| Blog Generation | Complete | Outline + Content agents with Gemini |
| Draft Management | Complete | CRUD operations, pagination |
| Approval Workflow | Complete | Admin review queue |
| Category System | Complete | User-specific categories |
| SEO Agent | Complete | Keyword analysis, readability scores |
| Formatting Agent | Complete | Markdown → HTML, TOC, reading time |
| Public Blog Site | Complete | User-facing published blog pages |
| Site Settings | Complete | Customizable site name, description |
| UI Refactoring | Complete | Consistent styling, external CSS/JS |

---

## 12. Key Design Decisions

1. **Multi-Agent Architecture**: Separating AI tasks into specialized agents (outline, content, SEO, formatting) allows for modular development and easier debugging.

2. **Firebase Over SQL**: Chose Firestore for rapid development, real-time capabilities, and seamless auth integration.

3. **Server-Side Rendering**: Jinja2 templates provide fast initial page loads and better SEO than SPAs.

4. **Optional SEO During Generation**: SEO analysis is disabled by default during blog generation for speed. Can be run separately.

5. **User-Specific Data**: All content (blogs, categories, settings) is scoped to individual users for multi-tenancy.

6. **Human-in-the-Loop**: Admin approval before publishing ensures content quality control.

---

## 13. License

This project is developed as a Final Year Project (FYP) for academic purposes.

---

*Last Updated: April 2026*
