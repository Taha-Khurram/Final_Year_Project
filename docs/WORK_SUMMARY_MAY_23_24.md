# Scriptly FYP - Work Summary (May 23-24, 2026)

---

## Day 1: May 23, 2026 (Yesterday)

### SEO Optimization Module (Major Feature)
- **Added full Optimization page** with URL analysis, SEO metrics display, routes, templates, and styling
- **Keyword Research** - Implemented keyword research tab with country selection, draft selection, keyword extraction via Gemini 3.0, and metrics fetching from Ahrefs API
- **Site Audit** - Added site audit functionality with domain extraction, API integration, and results display
- **Scrollable Audit Table** - Enhanced optimization page with scrollable data presentation
- **Auto Optimization** - Added one-click auto optimization for blog posts
- **SEO Reports** - Implemented report saving, fetching, deleting with reports tab and dropdown actions (details, export, delete)
- **Styling Polish** - Updated layout, scrollbar aesthetics, widths, and colors

### Blog Scheduling (Major Feature)
- **Weekly Calendar View** - Implemented full weekly calendar view for blog scheduling
- **Schedule Management** - Added save, update, and delete schedule entries with enhanced calendar fetching
- **Best Time Suggestions** - AI-powered best time recommendations for scheduling blogs
- **Published Stats** - Updated schedule entries to reflect published status, added published stats display
- **UI Refactor** - Updated CSS for stats layout, refactored JavaScript for performance, updated HTML modals

### Admin Dashboard Improvements
- **User Management** - Cleaned up modal structure and improved layout for user management modals
- **User Data Prefetching** - Implemented user data prefetching and caching for improved performance
- **Sidebar** - Added Optimization link to sidebar for easy access
- **Drafts** - Added copy draft content functionality and improved button actions in view modal

---

## Day 2: May 24, 2026 (Today)

### Site Settings Enhancements
- **Site Statistics** - Added site statistics section and published blogs management to site settings
- **Update Logic** - Enhanced site settings update logic with improved error handling in JavaScript

### Category Management
- **View Blogs in Category** - Implemented view blogs functionality for categories with modal display
- **Enhanced Status Display** - Added additional blog status states (UNDER_REVIEW, SCHEDULED, etc.) in category view

### Google Sheets Activity Agent (Major Feature - Current Session)
- **Rewrote `google_sheets_service.py`** - Complete rewrite with:
  - Single "Blogs" tab for ALL data (no separate worksheets)
  - Background write queue with flush worker (batches up to 20 rows)
  - `log_bulk_activities()` for frontend click events
  - `get_recent_activities()` for settings preview
  - `log_activity()`, `sync_user()`, `sync_blog()` all route to same tab
  
- **Created `activity-tracker.js`** - Frontend tracker that:
  - Captures every click via event delegation (buttons, links, tabs, modals, dropdowns)
  - Tracks page visits, form submissions, PJAX navigations
  - Batches events client-side, flushes every 5 seconds
  - Uses `sendBeacon` on page unload for reliable delivery
  - Exposes `window.ScriptlyTracker.enable()/disable()` control
  
- **Added API endpoints in `blog_routes.py`**:
  - `POST /api/track-activity` - Receives batched events, enriches with IP/session, writes to Sheets in background thread
  - `GET /api/sheets-recent-activity` - Returns last 10 entries for admin preview
  - Added `activity_tracking_enabled` field to site settings

- **Rewrote Google Sheets tab in `site_settings.html`**:
  - Uncommented and enhanced the tab with tracking toggle
  - Connection status badges (Connected/Tracking Active/Tracking Paused)
  - What-gets-tracked info panel
  - Service account sharing instructions
  - Live recent activity table with refresh button

- **Updated `base.html`** - Included tracker script globally on all admin pages

- **Updated `README.md`** - Added Google Sheets Activity Agent documentation

---

## Summary of Files Modified/Created

### New Files
| File | Description |
|------|-------------|
| `app/static/js/pages/activity-tracker.js` | Frontend click/action tracker |

### Modified Files
| File | Changes |
|------|---------|
| `app/services/google_sheets_service.py` | Complete rewrite - single tab, queue-based writes |
| `app/routes/blog_routes.py` | Added tracking endpoints + settings field |
| `app/templates/site_settings.html` | Uncommented & rewrote Google Sheets tab |
| `app/templates/base.html` | Added tracker script globally |
| `README.md` | Updated documentation for new features |

---

## Architecture: Google Sheets Activity Agent

```
┌─────────────────────────────────────────────────────────────┐
│                    ADMIN DASHBOARD                            │
│                                                              │
│  activity-tracker.js (loaded on every page)                  │
│  ├── Listens to ALL clicks (event delegation)               │
│  ├── Tracks page visits, form submits, tab switches         │
│  ├── Batches events in memory (max 25)                      │
│  ├── Flushes every 5s via POST /api/track-activity          │
│  └── sendBeacon on page unload                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               FLASK BACKEND                                   │
│                                                              │
│  POST /api/track-activity                                    │
│  ├── Checks activity_tracking_enabled in site settings       │
│  ├── Enriches events with IP, session ID, user info          │
│  ├── Spawns background thread                                │
│  └── Calls sheets.log_bulk_activities()                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            GOOGLE SHEETS SERVICE                              │
│                                                              │
│  Write Queue (thread-safe)                                   │
│  ├── Flush worker runs continuously                          │
│  ├── Batches up to 20 rows per API call                     │
│  └── append_rows() → always adds to bottom                  │
│                                                              │
│  Single "Blogs" Tab                                          │
│  ├── Headers: Timestamp | User | User ID | Action Type |    │
│  │            Action | Page | Element | Details |            │
│  │            IP Address | Session ID                        │
│  └── Every row appended to next available row               │
└─────────────────────────────────────────────────────────────┘
```

---

## Total Commits: 22 (May 23-24)
- **May 23**: 17 commits
- **May 24**: 5 commits + current uncommitted work (Google Sheets Activity Agent)
