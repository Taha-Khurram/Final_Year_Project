/**
 * Schedule Page — Weekly Calendar View
 */

let allBlogs = [];
let currentWeekStart = getWeekStart(new Date());
let rescheduleBlogId = null;
let selectedBlogId = null;
let availableBlogs = [];

document.addEventListener('DOMContentLoaded', () => {
  // Use prefetched data for instant render
  if (window.PREFETCHED_BLOGS && window.PREFETCHED_BLOGS.length > 0) {
    allBlogs = window.PREFETCHED_BLOGS;
    updateStats();
    renderWeekCalendar();
  } else if (window.PREFETCHED_BLOGS) {
    renderWeekCalendar();
  } else {
    loadScheduleData();
  }
  setupWeekNavigation();
  setupRescheduleModal();
  setupAddScheduleModal();
});

// ==================== WEEK HELPERS ====================

function getWeekStart(date) {
  const d = new Date(date);
  const day = d.getDay();
  d.setDate(d.getDate() - day);
  d.setHours(0, 0, 0, 0);
  return d;
}

function getWeekDays(weekStart) {
  const days = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    days.push(d);
  }
  return days;
}

function formatWeekTitle(weekStart) {
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekEnd.getDate() + 6);
  const opts = { month: 'short', day: 'numeric' };
  const startStr = weekStart.toLocaleDateString('en-US', opts);
  const endStr = weekEnd.toLocaleDateString('en-US', opts);
  const year = weekEnd.getFullYear();
  return `${startStr} – ${endStr}, ${year}`;
}

function isSameDay(d1, d2) {
  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate();
}

function isToday(date) {
  return isSameDay(date, new Date());
}

function getTimeBlock(hour) {
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 18) return 'afternoon';
  return 'evening';
}

// ==================== NAVIGATION ====================

function setupWeekNavigation() {
  document.getElementById('prevWeek').addEventListener('click', () => {
    currentWeekStart.setDate(currentWeekStart.getDate() - 7);
    updateWeekTitle();
    renderWeekCalendar();
  });

  document.getElementById('nextWeek').addEventListener('click', () => {
    currentWeekStart.setDate(currentWeekStart.getDate() + 7);
    updateWeekTitle();
    renderWeekCalendar();
  });

  document.getElementById('todayBtn').addEventListener('click', () => {
    currentWeekStart = getWeekStart(new Date());
    updateWeekTitle();
    renderWeekCalendar();
  });

  updateWeekTitle();
}

function updateWeekTitle() {
  document.getElementById('weekTitle').textContent = formatWeekTitle(currentWeekStart);
}

// ==================== DATA LOADING ====================

async function loadScheduleData() {
  try {
    const res = await fetch('/api/schedule/list');
    if (!res.ok) {
      renderEmptyCalendar();
      return;
    }

    const data = await res.json();
    if (data.success) {
      allBlogs = data.blogs;
      updateStats();
      renderWeekCalendar();
    } else {
      renderEmptyCalendar();
    }
  } catch (err) {
    console.error('Schedule load error:', err);
    renderEmptyCalendar();
  }
}

function updateStats() {
  const scheduled = allBlogs.filter(b => b.status === 'SCHEDULED').length;
  const weekDays = getWeekDays(currentWeekStart);
  const thisWeek = allBlogs.filter(b => {
    if (!b.scheduled_at) return false;
    const d = new Date(b.scheduled_at);
    return d >= weekDays[0] && d <= new Date(weekDays[6].getTime() + 86400000);
  }).length;

  document.getElementById('stat-scheduled').textContent = scheduled;
  document.getElementById('stat-month').textContent = thisWeek;
}

// ==================== WEEKLY CALENDAR RENDERING ====================

function renderWeekCalendar() {
  const container = document.getElementById('weeklyCalendar');
  const days = getWeekDays(currentWeekStart);
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const timeBlocks = [
    { key: 'morning', label: 'Morning', sub: '6 AM – 12 PM' },
    { key: 'afternoon', label: 'Afternoon', sub: '12 PM – 6 PM' },
    { key: 'evening', label: 'Evening', sub: '6 PM – 12 AM' }
  ];

  // Build grid HTML
  let html = '<div class="calendar-grid">';

  // Header row
  html += '<div class="calendar-header-row">';
  html += '<div class="calendar-header-spacer"></div>';
  days.forEach((day, i) => {
    const todayClass = isToday(day) ? ' is-today' : '';
    html += `<div class="calendar-day-header${todayClass}">
      <div class="day-name">${dayNames[i]}</div>
      <div class="day-number">${day.getDate()}</div>
    </div>`;
  });
  html += '</div>';

  // Time block rows
  timeBlocks.forEach(block => {
    html += '<div class="calendar-time-row">';
    html += `<div class="calendar-time-label">${block.label}</div>`;

    days.forEach(day => {
      const blogsInCell = getBlogsForCell(day, block.key);
      html += `<div class="calendar-cell" data-day="${day.toISOString().split('T')[0]}" data-block="${block.key}">`;
      blogsInCell.forEach(blog => {
        const time = new Date(blog.scheduled_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
        const isPublished = blog.status === 'PUBLISHED';
        const eventClass = isPublished ? 'calendar-event calendar-event-published' : 'calendar-event';

        let dropdownHtml = '';
        if (isPublished) {
          dropdownHtml = `<ul class="dropdown-menu dropdown-menu-end">
            <li><span class="dropdown-item text-success" style="cursor:default;">
              <i class="bi bi-check-circle-fill"></i> Published
            </span></li>
          </ul>`;
        } else {
          dropdownHtml = `<ul class="dropdown-menu dropdown-menu-end">
            <li><button class="dropdown-item" onclick="openReschedule('${blog.id}', '${escapeAttr(blog.title)}')">
              <i class="bi bi-calendar-event" style="color: var(--primary-color);"></i> Reschedule
            </button></li>
            <li><button class="dropdown-item" onclick="publishNow('${blog.id}')">
              <i class="bi bi-check-circle" style="color: #059669;"></i> Publish Now
            </button></li>
            <li><hr class="dropdown-divider"></li>
            <li><button class="dropdown-item text-danger" onclick="cancelSchedule('${blog.id}')">
              <i class="bi bi-x-circle"></i> Cancel Schedule
            </button></li>
          </ul>`;
        }

        html += `<div class="${eventClass}" data-blog-id="${blog.id}">
          <div class="calendar-event-title">${escapeHtml(blog.title)}</div>
          <div class="calendar-event-time">${time}${isPublished ? ' &check;' : ''}</div>
          <div class="event-dropdown">
            <div class="dropdown">
              <button class="btn-event-menu" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-three-dots"></i>
              </button>
              ${dropdownHtml}
            </div>
          </div>
        </div>`;
      });
      html += '</div>';
    });

    html += '</div>';
  });

  html += '</div>';
  container.innerHTML = html;
  updateStats();
}

function getBlogsForCell(day, blockKey) {
  return allBlogs.filter(blog => {
    if (!blog.scheduled_at) return false;
    const d = new Date(blog.scheduled_at);
    if (!isSameDay(d, day)) return false;
    const hour = d.getHours();
    return getTimeBlock(hour) === blockKey;
  });
}

function renderEmptyCalendar() {
  const container = document.getElementById('weeklyCalendar');
  container.innerHTML = `
    <div class="calendar-empty">
      <i class="bi bi-calendar-x"></i>
      <p>No scheduled blogs found.</p>
      <p class="empty-sub">Click "Add Schedule" to schedule a blog for publishing.</p>
    </div>`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ==================== RESCHEDULE MODAL ====================

function setupRescheduleModal() {
  document.getElementById('confirmRescheduleBtn').addEventListener('click', async () => {
    const dateTime = document.getElementById('rescheduleDateTime').value;
    if (!dateTime) {
      showToast({ type: 'error', title: 'Error', message: 'Please select a date and time.', duration: 3000 });
      return;
    }

    const btn = document.getElementById('confirmRescheduleBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Rescheduling...';

    try {
      const isoDate = new Date(dateTime).toISOString();
      const res = await fetch(`/api/schedule/${rescheduleBlogId}/reschedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheduled_at: isoDate })
      });
      const data = await res.json();

      if (data.success) {
        showToast({ type: 'success', title: 'Rescheduled', message: 'Blog rescheduled successfully.', duration: 3000 });
        bootstrap.Modal.getInstance(document.getElementById('rescheduleModal')).hide();
        loadScheduleData();
      } else {
        showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to reschedule.', duration: 4000 });
      }
    } catch (err) {
      showToast({ type: 'error', title: 'Error', message: 'Connection error.', duration: 4000 });
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-calendar-check"></i> Reschedule';
    }
  });
}

function openReschedule(blogId, title) {
  rescheduleBlogId = blogId;
  document.getElementById('reschedule-blog-title').textContent = title;

  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById('rescheduleDateTime').min = now.toISOString().slice(0, 16);
  document.getElementById('rescheduleDateTime').value = '';

  const modal = new bootstrap.Modal(document.getElementById('rescheduleModal'));
  modal.show();
  loadBestTimeSuggestions('bestTimeSuggestionsListReschedule');
}

// ==================== PUBLISH / CANCEL ====================

async function publishNow(blogId) {
  if (!confirm('Publish this blog immediately?')) return;

  try {
    const res = await fetch(`/api/schedule/${blogId}/publish-now`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      showToast({ type: 'success', title: 'Published!', message: 'Blog is now live on the site.', duration: 3000 });
      loadScheduleData();
    } else {
      showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to publish.', duration: 4000 });
    }
  } catch (err) {
    showToast({ type: 'error', title: 'Error', message: 'Connection error.', duration: 4000 });
  }
}

async function cancelSchedule(blogId) {
  if (!confirm('Cancel this scheduled blog? It will be moved back to drafts.')) return;

  try {
    const res = await fetch(`/api/schedule/${blogId}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      showToast({ type: 'warning', title: 'Cancelled', message: 'Schedule cancelled, blog moved to drafts.', duration: 3000 });
      loadScheduleData();
    } else {
      showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to cancel.', duration: 4000 });
    }
  } catch (err) {
    showToast({ type: 'error', title: 'Error', message: 'Connection error.', duration: 4000 });
  }
}

// ==================== ADD SCHEDULE MODAL ====================

function setupAddScheduleModal() {
  document.getElementById('addScheduleBtn').addEventListener('click', () => {
    selectedBlogId = null;
    document.getElementById('scheduleFormSection').style.display = 'none';
    document.getElementById('confirmScheduleBtn').disabled = true;
    document.getElementById('blogSearchInput').value = '';
    loadAvailableBlogs();
    const modal = new bootstrap.Modal(document.getElementById('addScheduleModal'));
    modal.show();
  });

  document.getElementById('blogSearchInput').addEventListener('input', (e) => {
    renderBlogList(e.target.value.trim().toLowerCase());
  });

  document.getElementById('confirmScheduleBtn').addEventListener('click', confirmScheduleBlog);
}

async function loadAvailableBlogs() {
  const container = document.getElementById('blogListContainer');
  container.innerHTML = `<div class="blog-list-loading">
    <div class="spinner-border spinner-border-sm text-primary"></div>
    <span>Loading blogs...</span>
  </div>`;

  try {
    const res = await fetch('/api/schedule/available-blogs');
    const data = await res.json();

    if (data.success) {
      availableBlogs = data.blogs;
      renderBlogList('');
    } else {
      container.innerHTML = `<div class="blog-list-empty"><i class="bi bi-exclamation-circle"></i>Failed to load blogs.</div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="blog-list-empty"><i class="bi bi-exclamation-circle"></i>Connection error.</div>`;
  }
}

function renderBlogList(search) {
  const container = document.getElementById('blogListContainer');
  let filtered = availableBlogs;

  if (search) {
    filtered = availableBlogs.filter(b =>
      b.title.toLowerCase().includes(search) ||
      b.author_name.toLowerCase().includes(search)
    );
  }

  if (filtered.length === 0) {
    container.innerHTML = `<div class="blog-list-empty">
      <i class="bi bi-file-earmark-x"></i>
      ${search ? 'No blogs match your search.' : 'No drafts or blogs pending approval.'}
    </div>`;
    return;
  }

  container.innerHTML = filtered.map(blog => {
    const statusClass = blog.status === 'DRAFT' ? 'badge-draft' : 'badge-review';
    const statusLabel = blog.status === 'DRAFT' ? 'Draft' : 'Approval';
    const selectedClass = selectedBlogId === blog.id ? ' selected' : '';

    return `<div class="blog-list-item${selectedClass}" onclick="selectBlogForSchedule('${blog.id}', '${escapeAttr(blog.title)}')">
      <div class="blog-list-item-info">
        <div class="blog-list-item-title">${escapeHtml(blog.title)}</div>
        <div class="blog-list-item-meta">
          <span><i class="bi bi-person"></i> ${escapeHtml(blog.author_name)}</span>
        </div>
      </div>
      <span class="blog-status-badge ${statusClass}">${statusLabel}</span>
    </div>`;
  }).join('');
}

function selectBlogForSchedule(blogId, blogTitle) {
  selectedBlogId = blogId;

  // Re-render list to show selection
  renderBlogList(document.getElementById('blogSearchInput').value.trim().toLowerCase());

  // Show schedule form
  const formSection = document.getElementById('scheduleFormSection');
  formSection.style.display = 'block';
  document.getElementById('selectedBlogInfo').innerHTML = `<i class="bi bi-file-earmark-text"></i> ${blogTitle}`;
  document.getElementById('confirmScheduleBtn').disabled = false;

  // Set min datetime
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById('scheduleDateTime').min = now.toISOString().slice(0, 16);
  document.getElementById('scheduleDateTime').value = '';

  // Load best time suggestions
  loadBestTimeSuggestions('bestTimeSuggestionsListAdd');
}

async function confirmScheduleBlog() {
  if (!selectedBlogId) return;

  const dateTime = document.getElementById('scheduleDateTime').value;
  if (!dateTime) {
    showToast({ type: 'error', title: 'Error', message: 'Please select a date and time.', duration: 3000 });
    return;
  }

  const btn = document.getElementById('confirmScheduleBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Scheduling...';

  try {
    const isoDate = new Date(dateTime).toISOString();
    const res = await fetch(`/api/schedule/${selectedBlogId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheduled_at: isoDate })
    });
    const data = await res.json();

    if (data.success) {
      showToast({ type: 'success', title: 'Scheduled!', message: data.message || 'Blog scheduled successfully.', duration: 3000 });
      bootstrap.Modal.getInstance(document.getElementById('addScheduleModal')).hide();
      loadScheduleData();
    } else {
      showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to schedule.', duration: 4000 });
    }
  } catch (err) {
    showToast({ type: 'error', title: 'Error', message: 'Connection error.', duration: 4000 });
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-calendar-check"></i> Schedule';
  }
}

// ==================== BEST TIME SUGGESTIONS ====================

const FALLBACK_SUGGESTIONS = [
  { day: "Tuesday", day_index: 2, hour: 10, display_time: "Tuesday, 10:00 AM", reasoning: "Tuesdays mid-morning have high engagement across most blogs" },
  { day: "Thursday", day_index: 4, hour: 14, display_time: "Thursday, 2:00 PM", reasoning: "Thursday afternoons are peak reading time for most audiences" },
  { day: "Wednesday", day_index: 3, hour: 9, display_time: "Wednesday, 9:00 AM", reasoning: "Mid-week mornings capture early readers checking content" }
];

async function loadBestTimeSuggestions(listElId) {
  const list = document.getElementById(listElId);

  list.innerHTML = `
    <div class="best-time-loading">
      <div class="spinner-border spinner-border-sm text-primary"></div>
      <span>Analyzing your traffic data...</span>
    </div>`;

  try {
    const res = await fetch('/api/schedule/best-time?t=' + Date.now());
    const data = await res.json();

    const inputId = listElId === 'bestTimeSuggestionsListAdd' ? 'scheduleDateTime' : 'rescheduleDateTime';

    if (data.success && data.suggestions && data.suggestions.length > 0) {
      renderSuggestionChips(list, data.suggestions, inputId, true);
    } else {
      renderSuggestionChips(list, FALLBACK_SUGGESTIONS, inputId, false, data.message || null);
    }
  } catch (err) {
    const inputId = listElId === 'bestTimeSuggestionsListAdd' ? 'scheduleDateTime' : 'rescheduleDateTime';
    renderSuggestionChips(list, FALLBACK_SUGGESTIONS, inputId, false, null);
  }
}

function renderSuggestionChips(listEl, suggestions, inputId, fromAnalytics, apiMessage) {
  let sourceLabel;
  if (fromAnalytics) {
    sourceLabel = '<span class="best-time-source"><i class="bi bi-check-circle-fill"></i> Based on your Google Analytics data (last 28 days)</span>';
  } else if (apiMessage) {
    sourceLabel = `<span class="best-time-source best-time-source-warning"><i class="bi bi-exclamation-triangle-fill"></i> ${apiMessage}</span>`;
  } else {
    sourceLabel = '<span class="best-time-source"><i class="bi bi-lightbulb-fill"></i> General best practices</span>';
  }

  listEl.innerHTML = sourceLabel + suggestions.map(s =>
    `<button type="button" class="best-time-chip" onclick="applyBestTime(${s.day_index}, ${s.hour}, '${inputId}')" title="${s.reasoning}">
      <i class="bi bi-clock"></i> ${s.display_time}
      <span class="best-time-score">${s.reasoning}</span>
    </button>`
  ).join('');
}

function applyBestTime(dayIndex, hour, inputId) {
  const now = new Date();
  const currentDay = now.getDay();
  let daysUntil = dayIndex - currentDay;
  if (daysUntil < 0) daysUntil += 7;
  if (daysUntil === 0 && hour <= now.getHours()) daysUntil = 7;

  const target = new Date(now);
  target.setDate(target.getDate() + daysUntil);
  target.setHours(hour, 0, 0, 0);

  const year = target.getFullYear();
  const month = String(target.getMonth() + 1).padStart(2, '0');
  const day = String(target.getDate()).padStart(2, '0');
  const hrs = String(target.getHours()).padStart(2, '0');

  document.getElementById(inputId).value = `${year}-${month}-${day}T${hrs}:00`;
}
