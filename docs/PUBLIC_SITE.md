# Public Site Documentation

The Public Site is a fully-featured, responsive blog website that Scriptly generates for each user. It provides a professional front-end for visitors to browse published blog content, subscribe to newsletters, and contact the site owner.

## Table of Contents

- [Overview](#overview)
- [Pages](#pages)
- [Site Settings](#site-settings)
- [URL Structure](#url-structure)
- [Features](#features)
- [Performance Optimizations](#performance-optimizations)
- [Templates](#templates)
- [Customization](#customization)

---

## Overview

Each user in Scriptly gets a unique public-facing blog site accessible at `/site/<user_id>`. The site is fully customizable through the Site Settings panel and includes:

- Modern, responsive design with gradient styling
- Mobile-first navigation
- Newsletter subscription system
- Contact form
- Category filtering and search
- SEO optimization
- Social sharing

---

## Pages

### 1. Home Page (`/site/<user_id>`)

The homepage serves as the landing page for visitors.

**Features:**
- Hero section with site name, description, and call-to-action buttons
- Statistics display (articles count, categories, readers)
- Featured posts grid (1 main + 2 secondary)
- Latest posts section with category pills
- Newsletter subscription form
- Niche badge display

**Template:** `site_home.html`

### 2. Blog Listing Page (`/site/<user_id>/blog`)

A dedicated page for browsing all published articles.

**Features:**
- Search bar for filtering articles by title
- Sort options (Latest, Oldest, Title A-Z)
- Pagination with customizable posts per page
- Sidebar with:
  - Category list with post counts
  - Newsletter subscription form
- Blog cards with category badges, excerpts, and dates

**Template:** `site_blog.html`

**Query Parameters:**
- `page` - Page number (default: 1)
- `category` - Filter by category name

### 3. Single Post Page (`/site/<user_id>/post/<blog_id>`)

Individual blog post view with full content.

**Features:**
- Article header with category, title, author, date, reading time
- Table of contents (auto-generated from headings)
- Full article content with markdown rendering
- Code syntax highlighting
- Social share buttons (Twitter, LinkedIn, Facebook)
- Related posts sidebar (same category)
- Back to all posts link

**Template:** `site_post.html`

### 4. About Page (`/site/<user_id>/about`)

Information about the site and its author.

**Features:**
- Hero section with logo/avatar and site description
- Niche badge
- Story section (customizable content)
- Values section (Quality Content, Community First, Authenticity)
- Statistics section (articles, categories, readers, availability)
- Call-to-action buttons

**Template:** `site_about.html`

### 5. Contact Page (`/site/<user_id>/contact`)

Contact form for visitor inquiries.

**Features:**
- Contact form (name, email, subject, message)
- Success/error message display
- Contact info sidebar (email, response time, website)
- Social links card
- FAQ section with common questions

**Template:** `site_contact.html`

### 6. Category Filter (`/site/<user_id>/category/<category_name>`)

Filtered view of posts by category.

**Features:**
- Uses home page template with filtered content
- Active category indicator
- Category sidebar navigation

---

## Site Settings

Site settings allow customization of the public site appearance and behavior.

### General Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `site_name` | Display name of the blog | "My Blog" |
| `site_description` | Short description/tagline | "Welcome to my blog" |
| `niche` | Site niche/category badge | "" |

### Appearance Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `logo_url` | URL to site logo image | "" |
| `favicon_url` | URL to favicon | "" |
| `primary_color` | Primary brand color (hex) | "#4318FF" |
| `cover_image_url` | Cover image URL | "" |

### Content Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `posts_per_page` | Number of posts per page | 10 |
| `default_language` | Site language code | "en" |
| `show_reading_time` | Display reading time on posts | true |
| `show_author` | Display author name on posts | true |
| `featured_post_id` | ID of featured post | "" |

### SEO Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `meta_title` | Custom meta title | "" |
| `meta_description` | Meta description for SEO | "" |
| `og_image_url` | Open Graph image URL | "" |
| `analytics_id` | Google Analytics ID | "" |

### Social & Contact Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `social_links.twitter` | Twitter profile URL | "" |
| `social_links.linkedin` | LinkedIn profile URL | "" |
| `social_links.github` | GitHub profile URL | "" |
| `contact_email` | Contact email address | "" |
| `about_content` | Custom about page content | "" |

### Behavior Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `site_visibility` | "public" or "unlisted" | "public" |

---

## URL Structure

```
/site/<user_id>                          # Home page
/site/<user_id>/blog                     # Blog listing
/site/<user_id>/blog?page=2              # Paginated blog
/site/<user_id>/blog?category=Tech       # Category filter
/site/<user_id>/post/<blog_id>           # Single post
/site/<user_id>/about                    # About page
/site/<user_id>/contact                  # Contact page
/site/<user_id>/category/<category_name> # Category archive
/site/<user_id>/subscribe                # Newsletter subscription (POST)
```

---

## Features

### Newsletter System

The newsletter subscription system is integrated throughout the site:

- **Subscription Forms:** Footer, blog sidebar, home page
- **Duplicate Prevention:** Existing subscribers see "Already Subscribed" modal
- **Success Modal:** New subscribers see a thank you modal
- **Async Handling:** Forms submit via fetch() without page reload

**Endpoint:** `POST /site/<user_id>/subscribe`

**Response:**
```json
{
  "success": true,
  "is_new": true,  // false if already subscribed
  "message": "Subscribed successfully!"
}
```

### Contact Form

Visitors can submit inquiries through the contact form.

**Fields:**
- Name (required)
- Email (required)
- Subject (required)
- Message (required)

**Endpoint:** `POST /site/<user_id>/contact`

Submissions are stored in Firestore for the site owner to review.

### Search & Sort

The blog listing page includes client-side search and sorting:

- **Search:** Filters posts by title as user types
- **Sort Options:**
  - Latest (default) - by date descending
  - Oldest - by date ascending
  - Title A-Z - alphabetical

### Social Sharing

Each blog post includes share buttons for:
- Twitter
- LinkedIn
- Facebook

Shares include the post title and URL.

### Table of Contents

Blog posts with multiple headings display an auto-generated table of contents:
- Extracted from H2 and H3 headings
- Clickable anchor links
- Displayed both inline (top of article) and in sidebar
- Nested hierarchy for H3 under H2

### Related Posts

Single post pages show related posts from the same category:
- Up to 3 related posts
- Displayed in sidebar
- Shows title and date

---

## Performance Optimizations

The public site includes several performance optimizations:

### 1. Response Compression (Flask-Compress)
- All responses are gzip compressed
- Reduces response size by 60-70%

### 2. Static Asset Caching (WhiteNoise)
- CSS, JS, and images cached for 7 days
- `Cache-Control: max-age=604800` header

### 3. In-Memory Caching
- Site settings cached for 2 minutes
- Published blogs cached for 2 minutes
- Reduces Firestore queries by ~80%

### 4. Cache Invalidation
- Settings cache cleared on update
- Blog cache cleared on status change

### 5. Link Prefetching (instant.page)
- Pages prefetched on link hover
- Makes navigation feel instant
- ~1KB library, module loaded

### 6. CDN Preconnect
- Preconnect hints for Bootstrap Icons CDN
- Reduces connection latency

---

## Templates

### Base Template (`site_base.html`)

The base template provides:
- HTML structure with SEO meta tags
- Open Graph / Twitter Card tags
- Dynamic primary color CSS variable
- Header with logo and navigation
- Mobile responsive hamburger menu
- Footer with:
  - Site branding
  - Quick links
  - Social links
  - Newsletter form
- Newsletter success/already-subscribed modals
- Google Analytics integration (if configured)

### Template Inheritance

```
site_base.html
├── site_home.html
├── site_blog.html
├── site_post.html
├── site_about.html
└── site_contact.html
```

### Template Blocks

| Block | Purpose |
|-------|---------|
| `title` | Page title |
| `extra_css` | Page-specific styles |
| `content` | Main page content |
| `extra_js` | Page-specific scripts |

---

## Customization

### Changing Primary Color

The primary color is set via site settings and applied through CSS variables:

```css
:root {
    --primary-color: {{ settings.primary_color or '#4318FF' }};
    --primary-light: {{ settings.primary_color or '#4318FF' }}15;
}
```

All UI elements use these variables for consistent theming.

### Adding Custom Content

**About Page:** Use the `about_content` setting to add custom HTML content to the about page story section.

**Featured Post:** Set `featured_post_id` to highlight a specific post on the home page.

### Adding Social Links

Configure social links in site settings:
- Twitter URL
- LinkedIn URL
- GitHub URL

Links appear in the header, footer, and contact page sidebar.

---

## Static Assets

### CSS (`/static/css/site/site.css`)

Contains all shared styles:
- CSS variables (colors, spacing, shadows, transitions)
- Header and navigation styles
- Footer styles
- Blog card components
- Hero sections
- Newsletter modals
- Responsive breakpoints

### JavaScript (`/static/js/site/site.js`)

Contains shared functionality:
- Mobile menu toggle
- Newsletter form handler
- Modal open/close functions
- Keyboard navigation (Escape to close modals)

---

## API Reference

### Public Routes (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/site/<user_id>` | Home page |
| GET | `/site/<user_id>/blog` | Blog listing |
| GET | `/site/<user_id>/post/<blog_id>` | Single post |
| GET | `/site/<user_id>/about` | About page |
| GET | `/site/<user_id>/contact` | Contact page |
| POST | `/site/<user_id>/contact` | Submit contact form |
| GET | `/site/<user_id>/category/<name>` | Category archive |
| POST | `/site/<user_id>/subscribe` | Newsletter signup |

---

## Database Collections

### `site_settings`
Stores per-user site configuration. Document ID is the user ID.

### `contact_submissions`
Stores contact form submissions with:
- `site_owner_id` - The user who owns the site
- `name`, `email`, `subject`, `message` - Form data
- `submitted_at` - Timestamp

### `newsletter_subscribers`
Stores newsletter subscriptions with:
- `site_owner_id` - The user who owns the site
- `email` - Subscriber email
- `subscribed_at` - Timestamp
- `status` - Active/unsubscribed

---

## Security Considerations

1. **No Authentication Required:** Public site routes are accessible without login
2. **Site Ownership Verification:** Posts are verified to belong to the site owner
3. **Unlisted Sites:** Can be set to `noindex, nofollow` via site_visibility
4. **Input Validation:** Contact form and newsletter inputs are validated
5. **XSS Protection:** Content is escaped by default in Jinja2 templates
6. **CSRF:** Forms use standard POST submissions (consider adding CSRF tokens for production)

---

## Browser Support

The public site is designed to work on:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome for Android)

Responsive breakpoints:
- Desktop: > 900px
- Tablet: 768px - 900px
- Mobile: < 768px
