/**
 * Schedule Page JavaScript
 */

let allBlogs = [];
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let rescheduleBlogId = null;

document.addEventListener('DOMContentLoaded', () => {
  loadScheduleData();
  setupNavigation();
  setupRescheduleModal();
});

function setupNavigation() {
  document.getElementById('prevMonth').addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    updateMonthTitle();
    renderTimeline();
  });

  document.getElementById('nextMonth').addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    updateMonthTitle();
    renderTimeline();
  });

  updateMonthTitle();
}

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

function updateMonthTitle() {
  const months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December'];
  document.getElementById('monthTitle').textContent = `${months[currentMonth]} ${currentYear}`;
}

async function loadScheduleData() {
  try {
    const res = await fetch('/api/schedule/list');
    const data = await res.json();

    if (data.success) {
      allBlogs = data.blogs;
      updateStats();
      renderTimeline();
    } else {
      showToast({ type: 'error', title: 'Error', message: 'Failed to load schedule data.', duration: 4000 });
    }
  } catch (err) {
    showToast({ type: 'error', title: 'Error', message: 'Connection error loading schedule.', duration: 4000 });
  }
}

function updateStats() {
  const scheduled = allBlogs.filter(b => b.status === 'SCHEDULED').length;

  const now = new Date();
  const thisMonth = allBlogs.filter(b => {
    if (!b.scheduled_at) return false;
    const d = new Date(b.scheduled_at);
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  }).length;

  document.getElementById('stat-scheduled').textContent = scheduled;
  document.getElementById('stat-month').textContent = thisMonth;
}

function renderTimeline() {
  const container = document.getElementById('timelineContainer');

  let filtered = allBlogs.filter(blog => {
    if (!blog.scheduled_at) return false;
    const d = new Date(blog.scheduled_at);
    return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="schedule-empty">
        <i class="bi bi-calendar-x"></i>
        <p>No scheduled blogs for this month.</p>
        <p class="empty-sub">Use the approval page to schedule blogs for future publishing.</p>
      </div>
    `;
    return;
  }

  const grouped = {};
  filtered.forEach(blog => {
    const d = new Date(blog.scheduled_at);
    const dateKey = d.toISOString().split('T')[0];
    if (!grouped[dateKey]) grouped[dateKey] = [];
    grouped[dateKey].push(blog);
  });

  const sortedDates = Object.keys(grouped).sort();

  let html = '';
  sortedDates.forEach(dateKey => {
    const d = new Date(dateKey + 'T00:00:00');
    const dateText = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const dayText = d.toLocaleDateString('en-US', { weekday: 'long' });

    html += `<div class="timeline-date-group">
      <div class="timeline-date-header">
        <div class="date-icon"><i class="bi bi-calendar3"></i></div>
        <span class="date-text">${dateText}</span>
        <span class="date-day">${dayText}</span>
      </div>`;

    grouped[dateKey].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));

    grouped[dateKey].forEach(blog => {
      const time = new Date(blog.scheduled_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

      html += `<div class="schedule-card" id="schedule-card-${blog.id}">
        <div class="schedule-card-time">${time}</div>
        <div class="schedule-card-info">
          <div class="schedule-card-title">${blog.title}</div>
          <div class="schedule-card-meta">
            <span><i class="bi bi-folder2"></i> ${blog.category}</span>
            <span><i class="bi bi-person"></i> ${blog.author}</span>
          </div>
        </div>
        <span class="schedule-badge badge-scheduled">Scheduled</span>
        <div class="schedule-card-actions">
          <div class="dropdown">
            <button class="btn-dropdown-trigger" type="button" data-bs-toggle="dropdown" aria-expanded="false">
              <i class="bi bi-three-dots-vertical"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><button class="dropdown-item" onclick="openReschedule('${blog.id}', '${blog.title.replace(/'/g, "\\'")}')">
                <i class="bi bi-calendar-event" style="color: var(--primary-color);"></i> Reschedule
              </button></li>
              <li><button class="dropdown-item" onclick="publishNow('${blog.id}')">
                <i class="bi bi-check-circle" style="color: #059669;"></i> Publish Now
              </button></li>
              <li><hr class="dropdown-divider"></li>
              <li><button class="dropdown-item text-danger" onclick="cancelSchedule('${blog.id}')">
                <i class="bi bi-x-circle"></i> Cancel Schedule
              </button></li>
            </ul>
          </div>
        </div>
      </div>`;
    });

    html += '</div>';
  });

  container.innerHTML = html;
}

function openReschedule(blogId, title) {
  rescheduleBlogId = blogId;
  document.getElementById('reschedule-blog-title').textContent = title;

  // Set min to now
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById('rescheduleDateTime').min = now.toISOString().slice(0, 16);
  document.getElementById('rescheduleDateTime').value = '';

  const modal = new bootstrap.Modal(document.getElementById('rescheduleModal'));
  modal.show();
}

async function publishNow(blogId) {
  if (!confirm('Publish this blog immediately?')) return;

  const card = document.getElementById(`schedule-card-${blogId}`);

  try {
    const res = await fetch(`/api/schedule/${blogId}/publish-now`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      showToast({ type: 'success', title: 'Published!', message: 'Blog is now live on the site.', duration: 3000 });
      if (card) {
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0';
        card.style.transform = 'translateX(20px)';
        setTimeout(() => { card.remove(); loadScheduleData(); }, 300);
      }
    } else {
      showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to publish.', duration: 4000 });
    }
  } catch (err) {
    showToast({ type: 'error', title: 'Error', message: 'Connection error.', duration: 4000 });
  }
}

async function cancelSchedule(blogId) {
  if (!confirm('Cancel this scheduled blog? It will be moved back to drafts.')) return;

  const card = document.getElementById(`schedule-card-${blogId}`);

  try {
    const res = await fetch(`/api/schedule/${blogId}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      showToast({ type: 'warning', title: 'Cancelled', message: 'Schedule cancelled, blog moved to drafts.', duration: 3000 });
      if (card) {
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0';
        card.style.transform = 'translateX(20px)';
        setTimeout(() => { card.remove(); loadScheduleData(); }, 300);
      }
    } else {
      showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to cancel.', duration: 4000 });
    }
  } catch (err) {
    showToast({ type: 'error', title: 'Error', message: 'Connection error.', duration: 4000 });
  }
}
