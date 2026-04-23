# Scriptly - Setup Guide

Complete setup guide for running Scriptly locally or in production.

---

## Prerequisites

- Python 3.9+
- Firebase project with Firestore enabled
- Google Cloud project with Gemini API enabled
- (Optional) Resend account for newsletter emails
- (Optional) RapidAPI account for SEO keyword research

---

## 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/Taha-Khurram/Final_Year_Project.git
cd Final_Year_Project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Firebase Setup

### 2.1 Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable **Firestore Database** (start in test mode for development)
4. Enable **Authentication** with Email/Password and Google sign-in providers

### 2.2 Generate Service Account Key
1. Go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save as `serviceAccountKey.json` in project root

### 2.3 Firestore Collections
The following collections will be created automatically:
- `blogs` - Blog posts and drafts
- `users` - User accounts
- `categories` - Blog categories
- `site_settings` - Public site configuration
- `newsletter_subscribers` - Email subscribers
- `newsletter_history` - Sent newsletters
- `newsletter_drafts` - Draft newsletters
- `activity_log` - User activity tracking
- `contacts` - Contact form submissions

---

## 3. Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to your `.env` file as `GEMINI_API_KEY`

---

## 4. Environment Variables

Create a `.env` file in the project root:

```env
# Required
FIREBASE_SERVICE_ACCOUNT=serviceAccountKey.json
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_flask_secret_key

# Optional - Newsletter emails (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxx

# Optional - SEO keyword research
RAPIDAPI_KEY=your_rapidapi_key
```

### Getting a Secret Key
Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. Email Service Setup (Optional)

For newsletter functionality, set up [Resend](https://resend.com/):

1. Create a free Resend account (100 emails/day free)
2. Add and verify your domain
3. Create an API key
4. Add `RESEND_API_KEY` to your `.env` file

Without this, newsletter generation still works but emails won't be sent.

---

## 6. SEO API Setup (Optional)

For advanced keyword research:

1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to [Google Search API](https://rapidapi.com/herosAPI/api/google-search74) (free tier: 500 requests/month)
3. Add `RAPIDAPI_KEY` to your `.env` file

Without this, SEO features use fallback methods (PyTrends, AI estimation).

---

## 7. Run the Application

### Development
```bash
python app.py
```
Access at `http://localhost:5000`

### Production
```bash
# Using Gunicorn (Linux/Mac)
gunicorn wsgi:app -w 4 -b 0.0.0.0:8000

# Using Waitress (Windows)
waitress-serve --port=8000 wsgi:app
```

---

## 8. First-Time Setup

1. Open `http://localhost:5000/signup`
2. Create your account
3. Go to Dashboard > Site Settings to configure your public blog
4. Start creating content!

### User Roles
- **USER**: Create blogs, submit for approval
- **ADMIN**: Approve/publish blogs, manage users

To make a user admin, update their `role` field in Firestore `users` collection to `"ADMIN"`.

---

## 9. Project Structure

```
FYP-main/
├── app/
│   ├── agents/              # AI agents (blog, SEO, newsletter, etc.)
│   ├── firebase/            # Firebase configuration & services
│   ├── routes/              # API routes
│   ├── services/            # External services (email)
│   ├── static/              # CSS, JS, images
│   ├── templates/           # HTML templates
│   └── utils/               # Utilities (caching, parallel)
├── docs/                    # Documentation
├── config.py                # App configuration
├── app.py                   # Entry point
├── wsgi.py                  # WSGI entry
└── requirements.txt         # Dependencies
```

---

## 10. API Quick Reference

### Blog Management
- `POST /api/generate` - Generate blog from topic
- `GET /api/get_blog/<id>` - Get blog by ID
- `POST /api/update_status/<id>` - Change blog status

### SEO Tools
- `POST /api/seo/analyze` - Analyze content
- `POST /api/seo/keywords` - Research keywords

### Newsletter
- `POST /api/newsletter/generate` - Generate newsletter from blogs
- `POST /api/newsletter/send` - Send to subscribers
- `GET /api/newsletter/subscribers` - List subscribers

### Public Site
- `GET /site/<user_id>` - Public blog homepage
- `GET /site/<user_id>/post/<blog_id>` - Single post
- `POST /site/<user_id>/subscribe` - Newsletter signup

---

## Troubleshooting

### Firebase Connection Issues
- Verify `serviceAccountKey.json` path in `.env`
- Check Firestore rules allow read/write

### Gemini API Errors
- Verify API key is valid
- Check quota limits in Google Cloud Console

### Email Not Sending
- Verify Resend API key
- Check domain verification status
- Review Resend dashboard for errors

---

## Support

For issues, open a ticket at [GitHub Issues](https://github.com/Taha-Khurram/Final_Year_Project/issues).

---

*Last Updated: April 2026*
