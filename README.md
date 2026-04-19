# Scriptly

An AI-powered blog content generation platform built with Flask and Google Gemini.

## Features

- **AI Blog Generation**: Automatically generate blog outlines and full content using Google Gemini
- **User Authentication**: Firebase-based authentication with Google sign-in support
- **Draft Management**: Save, edit, and manage blog drafts
- **Approval Queue**: Review and approve generated content before publishing
- **Category Management**: Organize blogs by categories
- **User Management**: Admin controls for managing users

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth
- **AI**: Google Generative AI (Gemini)
- **Deployment**: Gunicorn / Waitress

## Project Structure

```
├── app/
│   ├── agents/           # AI agents for content generation
│   │   ├── blog_agent.py
│   │   ├── outline_agent.py
│   │   ├── content_agent.py
│   │   └── ...
│   ├── firebase/         # Firebase configuration
│   ├── routes/           # API routes
│   ├── static/           # CSS, JS, images
│   └── templates/        # HTML templates
├── config.py
├── app.py
└── requirements.txt
```

## Setup

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

- `FIREBASE_SERVICE_ACCOUNT` - Path to Firebase service account JSON
- `GEMINI_API_KEY` - Google Gemini API key
- `SECRET_KEY` - Flask secret key

## License

This project is part of a Final Year Project (FYP).
