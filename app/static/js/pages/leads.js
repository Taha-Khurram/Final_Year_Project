/**
 * Leads Dashboard - leads.js
 * Handles leads listing, filtering, pagination, view, mark read, delete
 */

let currentFilter = 'all';
let currentSearch = '';
let currentPage = 1;
const perPage = 10;
let searchTimeout = null;
let currentLeadId = null;
let leadsCache = {};

document.addEventListener('DOMContentLoaded', function () {
    setupFilterTabs();
    setupSearch();
    setupModals();
    loadLeads();
});

// ==================== FILTER TABS ====================

function setupFilterTabs() {
    document.querySelectorAll('.leads-filter-tabs .filter-tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.leads-filter-tabs .filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.filter;
            currentPage = 1;
            loadLeads();
        });
    });
}

// ==================== SEARCH ====================

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearch = this.value.trim();
            currentPage = 1;
            loadLeads();
        }, 300);
    });
}

// ==================== MODALS ====================

function setupModals() {
    document.getElementById('modalDeleteBtn').addEventListener('click', function () {
        if (currentLeadId) {
            closeViewModal();
            setTimeout(() => showDeleteConfirm(currentLeadId), 200);
        }
    });

    document.getElementById('confirmDeleteBtn').addEventListener('click', function () {
        if (currentLeadId) {
            deleteLead(currentLeadId);
        }
    });
}

// ==================== LOAD LEADS ====================

async function loadLeads() {
    const listEl = document.getElementById('leadsList');
    listEl.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border spinner-border-sm text-primary opacity-50"></div>
            <p class="text-secondary fw-medium mt-2 mb-0">Loading leads...</p>
        </div>`;

    try {
        const params = new URLSearchParams({ page: currentPage });
        if (currentFilter !== 'all') params.set('status', currentFilter);
        if (currentSearch) params.set('search', currentSearch);

        const res = await fetch('/api/leads?' + params.toString());
        const data = await res.json();

        if (data.success) {
            renderLeads(data.submissions, data.total);
            renderPagination(data.page, data.total_pages);
        } else {
            listEl.innerHTML = renderEmpty();
        }
    } catch (err) {
        console.error('Error loading leads:', err);
        listEl.innerHTML = renderEmpty();
    }
}

// ==================== RENDER LEADS ====================

function renderLeads(leads, total) {
    const listEl = document.getElementById('leadsList');

    if (!leads || leads.length === 0) {
        listEl.innerHTML = renderEmpty();
        return;
    }

    leadsCache = {};
    leads.forEach(lead => { leadsCache[lead.id] = lead; });

    listEl.innerHTML = leads.map(lead => {
        const isUnread = !lead.read;
        const dateStr = formatDate(lead.created_at);

        return `
            <div class="lead-row ${isUnread ? 'unread' : ''}" data-id="${lead.id}" onclick="viewLeadById('${lead.id}')">
                <div class="col-lead-status">
                    <div class="lead-status-dot"></div>
                </div>
                <div class="col-lead-name">
                    <span class="lead-name">${escapeHtml(lead.name || 'Unknown')}</span>
                </div>
                <div class="col-lead-email">
                    <span class="lead-email">${escapeHtml(lead.email || '')}</span>
                </div>
                <div class="col-lead-subject">
                    <span class="lead-subject">${escapeHtml(lead.subject || 'No subject')}</span>
                </div>
                <div class="col-lead-date">
                    <span class="lead-date">${dateStr}</span>
                </div>
                <div class="col-lead-actions" onclick="event.stopPropagation()">
                    <div class="lead-dropdown">
                        <button class="lead-dots-btn" onclick="toggleDropdown(event, '${lead.id}')">
                            <i class="bi bi-three-dots-vertical"></i>
                        </button>
                        <div class="lead-dropdown-menu" id="dropdown-${lead.id}">
                            <button class="dropdown-item" onclick="viewLeadById('${lead.id}')">
                                <i class="bi bi-eye"></i> View
                            </button>
                            ${isUnread ? `<button class="dropdown-item" onclick="markAsRead('${lead.id}')">
                                <i class="bi bi-envelope-open"></i> Mark as Read
                            </button>` : ''}
                            <button class="dropdown-item dropdown-item-danger" onclick="showDeleteConfirm('${lead.id}')">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
    }).join('');
}

function renderEmpty() {
    let message = 'No leads yet';
    if (currentFilter === 'unread') message = 'No unread leads';
    else if (currentFilter === 'read') message = 'No read leads';
    if (currentSearch) message = 'No leads match your search';

    return `
        <div class="leads-empty">
            <div class="leads-empty-icon"><i class="bi bi-person-lines-fill"></i></div>
            <div class="leads-empty-title">${message}</div>
            <div class="leads-empty-text">Contact form submissions will appear here.</div>
        </div>`;
}

// ==================== PAGINATION ====================

function renderPagination(page, totalPages) {
    const container = document.getElementById('leadsPagination');
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button class="page-btn" ${page <= 1 ? 'disabled' : ''} onclick="goToPage(${page - 1})"><i class="bi bi-chevron-left"></i></button>`;

    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);

    if (start > 1) {
        html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (start > 2) html += `<span style="color:#94a3b8;padding:0 0.3rem;">...</span>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (end < totalPages) {
        if (end < totalPages - 1) html += `<span style="color:#94a3b8;padding:0 0.3rem;">...</span>`;
        html += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    html += `<button class="page-btn" ${page >= totalPages ? 'disabled' : ''} onclick="goToPage(${page + 1})"><i class="bi bi-chevron-right"></i></button>`;

    container.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadLeads();
}

// ==================== DROPDOWN ====================

function toggleDropdown(event, id) {
    event.stopPropagation();
    closeAllDropdowns();
    const menu = document.getElementById('dropdown-' + id);
    if (menu) menu.classList.toggle('show');
}

function closeAllDropdowns() {
    document.querySelectorAll('.lead-dropdown-menu.show').forEach(m => m.classList.remove('show'));
}

document.addEventListener('click', closeAllDropdowns);

// ==================== VIEW LEAD ====================

function viewLeadById(id) {
    const lead = leadsCache[id];
    if (!lead) return;
    viewLead(id, lead);
}

function viewLead(id, lead) {
    currentLeadId = id;

    document.getElementById('modalLeadSubject').textContent = lead.subject || 'No subject';
    document.getElementById('modalLeadName').textContent = lead.name || 'Unknown';
    document.getElementById('modalLeadEmail').textContent = lead.email || '';
    document.getElementById('modalLeadDate').textContent = formatDate(lead.created_at);
    document.getElementById('modalLeadMessage').textContent = lead.message || '';

    document.getElementById('viewLeadOverlay').classList.add('active');

    if (!lead.read) {
        markAsRead(id);
    }
}

function closeViewModal(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('viewLeadOverlay').classList.remove('active');
}

// ==================== MARK AS READ ====================

async function markAsRead(id) {
    try {
        await fetch(`/api/leads/${id}/read`, { method: 'POST' });
        refreshStats();
        const row = document.querySelector(`.lead-row[onclick*="${id}"]`);
        if (row) {
            row.classList.remove('unread');
        }
    } catch (err) {
        console.error('Error marking as read:', err);
    }
}

// ==================== DELETE ====================

function showDeleteConfirm(id) {
    currentLeadId = id;
    const btn = document.getElementById('confirmDeleteBtn');
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-trash"></i> Delete';
    document.getElementById('deleteLeadOverlay').classList.add('active');
}

function closeDeleteModal(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('deleteLeadOverlay').classList.remove('active');
}

async function deleteLead(id) {
    const btn = document.getElementById('confirmDeleteBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Deleting...';

    try {
        const res = await fetch(`/api/leads/${id}/delete`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            closeDeleteModal();
            currentLeadId = null;
            loadLeads();
            refreshStats();
        } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-trash"></i> Delete';
        }
    } catch (err) {
        console.error('Error deleting lead:', err);
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash"></i> Delete';
    }
}

// ==================== REFRESH STATS ====================

async function refreshStats() {
    try {
        const res = await fetch('/api/leads/stats');
        const data = await res.json();
        if (data.success) {
            document.getElementById('stat-total').textContent = data.stats.total;
            document.getElementById('stat-unread').textContent = data.stats.unread;
            document.getElementById('stat-read').textContent = data.stats.read;
        }
    } catch (err) {
        console.error('Error refreshing stats:', err);
    }
}

// ==================== UTILITIES ====================

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
