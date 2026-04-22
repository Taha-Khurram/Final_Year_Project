# Scriptly - Advanced Features Implementation Plan

## Current Status (Core System - Complete)

- [x] Blog Input & Triggering (website form)
- [x] AI Blog Draft Generation (OutlineAgent + ContentAgent)
- [x] Admin Approval Workflow
- [x] Category Management
- [x] User Authentication (Firebase)
- [x] Admin Dashboard
- [x] Draft Management

---

## Advanced Features (To Be Implemented)

### 1. SEO Agent
**Purpose:** Suggests SEO, readability, and tone improvements for blog drafts.

**Features:**
- Keyword density analysis
- Meta description generation
- Title tag optimization
- Readability score (Flesch-Kincaid)
- Heading structure validation (H1, H2, H3)
- Internal/external linking suggestions
- Image alt-text recommendations

**Implementation:**
```
app/agents/seo_agent.py
```

**API Endpoint:**
```
POST /api/blog/seo-analyze
GET /api/blog/<draft_id>/seo-suggestions
```

---

### 2. Formatting Agent
**Purpose:** Ensures consistent formatting and professional presentation of blog content.

**Features:**
- Markdown to HTML conversion with styling
- Consistent heading hierarchy
- Paragraph spacing optimization
- Bullet/numbered list formatting
- Code block detection and highlighting
- Quote formatting
- Table of contents generation
- Reading time calculation

**Implementation:**
```
app/agents/formatting_agent.py
```

**API Endpoint:**
```
POST /api/blog/format
GET /api/blog/<draft_id>/formatted
```

---

### 3. AI Best-Time Publishing
**Purpose:** Predicts optimal publishing times for maximum audience engagement.

**Features:**
- Analyze historical engagement data
- Category-based timing recommendations
- Day-of-week optimization
- Time zone considerations
- Scheduled publishing queue

**Implementation:**
```
app/agents/publishing_agent.py
```

**API Endpoint:**
```
GET /api/blog/<draft_id>/best-publish-time
POST /api/blog/<draft_id>/schedule
```

---

### 4. Semantic Search
**Purpose:** Natural language search across all published blogs.

**Features:**
- Vector embeddings for blog content
- Similarity-based search
- Search by topic/concept (not just keywords)
- Related posts suggestions
- Search result ranking

**Implementation:**
```
app/agents/search_agent.py
```

**Dependencies:**
- sentence-transformers (for embeddings)
- faiss or chromadb (for vector storage)

**API Endpoint:**
```
GET /api/search?q=<natural_language_query>
GET /api/blog/<blog_id>/related
```

---

### 5. AI-Generated Newsletter
**Purpose:** Automatically creates weekly/monthly newsletters from top-performing blogs.

**Features:**
- Select top blogs by engagement/views
- Generate newsletter summary
- Email-friendly HTML formatting
- Subscriber management
- Scheduled newsletter dispatch

**Implementation:**
```
app/agents/newsletter_agent.py
```

**API Endpoint:**
```
POST /api/newsletter/generate
GET /api/newsletter/preview
POST /api/newsletter/send
```

---

### 6. Smart Comment Moderation
**Purpose:** Detects spam/toxic comments and summarizes discussions.

**Features:**
- Spam detection
- Toxicity/profanity filtering
- Sentiment analysis
- Discussion summarization for admin
- Auto-approve safe comments
- Flag suspicious comments for review

**Implementation:**
```
app/agents/moderation_agent.py
```

**API Endpoint:**
```
POST /api/comments/moderate
GET /api/blog/<blog_id>/comment-summary
```

---

## Agent Architecture

```
app/agents/
├── __init__.py
├── blog_agent.py          # Existing - orchestrates outline + content
├── outline_agent.py       # Existing - generates blog outline
├── content_agent.py       # Existing - expands outline to full content
├── category_agent.py      # Existing - category suggestions
├── approval_agent.py      # Existing - approval workflow
├── drafts_agent.py        # Existing - draft management
├── seo_agent.py           # NEW - SEO optimization
├── formatting_agent.py    # NEW - content formatting
├── publishing_agent.py    # NEW - best-time publishing
├── search_agent.py        # NEW - semantic search
├── newsletter_agent.py    # NEW - newsletter generation
└── moderation_agent.py    # NEW - comment moderation
```

---

## Updated Pipeline Flow

```
User Input (Topic/Keywords)
        │
        ▼
┌───────────────────┐
│   Outline Agent   │  ──► Generate structured outline
└───────────────────┘
        │
        ▼
┌───────────────────┐
│   Content Agent   │  ──► Expand to full blog content
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Formatting Agent  │  ──► Clean formatting, TOC, reading time
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    SEO Agent      │  ──► Optimize for search engines
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Category Agent   │  ──► Suggest categories & tags
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Publishing Agent  │  ──► Recommend best publish time
└───────────────────┘
        │
        ▼
    [Draft Created]
        │
        ▼
┌───────────────────┐
│  Admin Approval   │  ──► Human-in-the-loop review
└───────────────────┘
        │
        ▼
    [Published Blog]
        │
        ▼
┌───────────────────┐
│  Search Agent     │  ──► Index for semantic search
└───────────────────┘
```

---

## Database Schema Updates (Firestore)

### blogs collection
```javascript
{
  id: string,
  title: string,
  content: string,           // Raw markdown
  formatted_html: string,    // Formatted HTML output
  outline: array,
  status: "draft" | "approved" | "published" | "rejected",
  category_id: string,
  tags: array,
  seo_data: {
    meta_description: string,
    keywords: array,
    readability_score: number,
    seo_score: number
  },
  publishing_data: {
    best_time: timestamp,
    scheduled_time: timestamp,
    actual_published: timestamp
  },
  engagement: {
    views: number,
    comments: number,
    shares: number
  },
  created_at: timestamp,
  updated_at: timestamp
}
```

### comments collection
```javascript
{
  id: string,
  blog_id: string,
  user_id: string,
  content: string,
  status: "pending" | "approved" | "spam" | "toxic",
  sentiment: "positive" | "neutral" | "negative",
  moderation_score: number,
  created_at: timestamp
}
```

### newsletters collection
```javascript
{
  id: string,
  title: string,
  content_html: string,
  blog_ids: array,
  status: "draft" | "sent",
  sent_at: timestamp,
  recipient_count: number
}
```

---

## Dependencies to Add

```txt
# requirements.txt additions
sentence-transformers>=2.2.0    # Semantic search embeddings
chromadb>=0.4.0                 # Vector database
textstat>=0.7.3                 # Readability analysis
beautifulsoup4>=4.12.0          # HTML parsing
markdown>=3.5.0                 # Markdown processing
better-profanity>=0.7.0         # Profanity detection
```

---

## Implementation Priority

| Priority | Feature | Complexity | Dependencies |
|----------|---------|------------|--------------|
| 1 | SEO Agent | Medium | textstat |
| 2 | Formatting Agent | Low | markdown, beautifulsoup4 |
| 3 | Semantic Search | High | sentence-transformers, chromadb |
| 4 | Best-Time Publishing | Medium | Analytics data |
| 5 | Comment Moderation | Medium | better-profanity |
| 6 | Newsletter Generation | Medium | Email service |

---

## Next Steps

1. **Phase 1:** Implement SEO Agent + Formatting Agent
2. **Phase 2:** Integrate into existing blog pipeline
3. **Phase 3:** Add Semantic Search
4. **Phase 4:** Implement Best-Time Publishing
5. **Phase 5:** Add Comment Moderation
6. **Phase 6:** Newsletter Generation

---

## WhatsApp Integration (Future)

The proposal mentions WhatsApp as an input channel. This can be implemented using:
- Twilio WhatsApp API
- n8n workflow automation
- Webhook endpoint to receive messages

```
POST /api/webhook/whatsapp
```
