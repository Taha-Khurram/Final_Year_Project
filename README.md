# Scriptly

An AI-powered blog content generation platform built with Flask and Google Gemini. Scriptly automates the entire blog creation workflow from topic input to SEO-optimized, publication-ready content.

## Features

### Core Features
- **AI Blog Generation**: Automatically generate blog outlines and full content using Google Gemini
- **User Authentication**: Firebase-based authentication with Google sign-in support
- **Draft Management**: Save, edit, and manage blog drafts
- **Approval Queue**: Review and approve generated content before publishing
- **Category Management**: Organize blogs by categories
- **User Management**: Admin controls for managing users

### Advanced Features
- **SEO Agent**: Comprehensive SEO analysis including keyword optimization, meta descriptions, readability scores (Flesch-Kincaid), and heading structure validation
- **Formatting Agent**: Professional content formatting with Markdown to HTML conversion, table of contents generation, reading time calculation, and consistent styling
- **Real-time SEO Tools**: Live content analysis with keyword density, word count, and optimization suggestions
- **Parallel Processing**: Efficient content generation with caching and parallel execution utilities

### Newsletter System
- **AI Newsletter Generation**: Automatically create engaging newsletters from published blogs using Gemini AI
- **Email Sending**: Send newsletters to subscribers via Resend API
- **Subscriber Management**: Track and manage newsletter subscribers
- **Newsletter History**: View and manage sent newsletters with full content preview
- **Draft Saving**: Save newsletter drafts for later editing
- **Subject Line Variations**: AI-generated alternative subject lines

### Public Blog Site
- **Modern Design**: Professional, responsive public-facing blog with hero sections and gradient styling
- **Multiple Pages**: Home, Blog (with pagination), About, and Contact pages
- **Mobile-First**: Responsive navigation with hamburger menu for mobile devices
- **Contact Form**: Visitor contact form with Firestore storage
- **Newsletter Signup**: Email subscription with duplicate prevention
- **Site Settings**: Customizable site name, description, colors, social links, and SEO metadata
- **Category Filtering**: Browse posts by category with sidebar navigation
- **Search & Sort**: Client-side search and sorting on the blog listing page

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth
- **AI**: Google Generative AI (Gemini)
- **Email**: Resend API
- **SEO Analysis**: RapidAPI (Google Search, Keyword Research)
- **Deployment**: Gunicorn / Waitress

## Project Structure

```
├── app/
│   ├── agents/           # AI agents for content generation
│   │   ├── blog_agent.py
│   │   ├── outline_agent.py
│   │   ├── content_agent.py
│   │   ├── seo_agent.py
│   │   ├── formatting_agent.py
│   │   ├── newsletter_agent.py
│   │   └── ...
│   ├── firebase/         # Firebase configuration
│   ├── routes/           # API routes
│   │   ├── blog_routes.py
│   │   ├── site_routes.py
│   │   ├── newsletter_routes.py
│   │   └── ...
│   ├── services/         # External services
│   │   └── email_service.py
│   ├── static/           # CSS, JS, images
│   ├── templates/        # HTML templates
│   │   ├── partials/     # Reusable template components
│   │   ├── site/         # Public blog site templates
│   │   └── emails/       # Email templates
│   └── utils/            # Utility modules (caching, parallel processing)
├── docs/                 # Documentation
├── config.py
├── app.py
└── requirements.txt
```

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/Taha-Khurram/Final_Year_Project.git
   cd Final_Year_Project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Firebase and Gemini API credentials
   ```

5. Run the application:
   ```bash
   python app.py
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_SERVICE_ACCOUNT` | Path to Firebase service account JSON | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `RESEND_API_KEY` | Resend API key for newsletters | Optional |
| `RAPIDAPI_KEY` | RapidAPI key for SEO tools | Optional |

## API Endpoints

### Blog Management
- `POST /api/blog/generate` - Generate blog content from topic
- `GET /api/blog/<draft_id>` - Get draft details
- `POST /api/blog/<draft_id>/approve` - Approve a draft

### SEO Tools
- `POST /api/blog/seo-analyze` - Analyze content for SEO
- `GET /api/blog/<draft_id>/seo-suggestions` - Get SEO suggestions for draft

### Formatting
- `POST /api/blog/format` - Format content with professional styling
- `GET /api/blog/<draft_id>/formatted` - Get formatted version of draft

### Newsletter
- `POST /api/newsletter/generate` - Generate newsletter from blogs
- `POST /api/newsletter/render` - Render newsletter HTML
- `POST /api/newsletter/send` - Send newsletter to subscribers
- `GET /api/newsletter/subscribers` - Get subscriber list
- `GET /api/newsletter/history` - Get sent newsletter history
- `GET /api/newsletter/drafts` - Get saved drafts

### Public Site
- `GET /site/<user_id>` - Public blog homepage
- `GET /site/<user_id>/blog` - Paginated blog listing with search
- `GET /site/<user_id>/post/<blog_id>` - Single blog post view
- `GET /site/<user_id>/about` - About page
- `GET /site/<user_id>/contact` - Contact page
- `POST /site/<user_id>/contact` - Submit contact form
- `POST /site/<user_id>/subscribe` - Newsletter subscription

## Documentation

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

## License

This project is part of a Final Year Project (FYP).

## Author

Taha Khurram - [GitHub](https://github.com/Taha-Khurram)
