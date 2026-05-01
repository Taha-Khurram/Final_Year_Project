/**
 * Comment Moderation Dashboard - comments.js
 * Handles comment listing, filtering, modals, editing, and deletion
 */

let currentFilter = 'all';
let currentPage = 1;
let currentCommentId = null;
const perPage = 15;

document.addEventListener('DOMContentLoaded', function () {
    setupFilterTabs();
    setupModalTabs();
    loadComments();
});

// ==================== FILTER TABS ====================

function setupFilterTabs() {
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.filter;
            currentPage = 1;
            loadComments();
        });
    });
}

// ==================== MODAL TABS ====================

function setupModalTabs() {
    document.querySelectorAll('.comment-modal-tabs .tab-item').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.comment-modal-tabs .tab-item').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#commentModal .tab-content').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('tab-' + this.dataset.tab).classList.add('active');

            // Show/hide save button based on active tab
            const saveBtn = document.getElementById('modal-save-edit');
            saveBtn.style.display = this.dataset.tab === 'edit' ? '' : 'none';
        });
    });
}

// ==================== LOAD COMMENTS ====================

async function loadComments() {
    const tbody = document.getElementById('comments-table-body');
    tbody.innerHTML = `
        <div class="text-center py-4 text-secondary">
            <div class="spinner-border spinner-border-sm"></div> Loading comments...
        </div>`;

    try {
        const params = new URLSearchParams({ page: currentPage, per_page: perPage });
        if (currentFilter !== 'all') params.set('status', currentFilter);

        const res = await fetch('/api/comments?' + params.toString());
        const data = await res.json();

        if (data.success && data.comments && data.comments.length > 0) {
            tbody.innerHTML = data.comments.map(renderCommentRow).join('');
            renderPagination(data.total, data.page, data.per_page);
        } else {
            tbody.innerHTML = `
                <div class="text-center py-5">
                    <div class="mb-3 text-muted opacity-50"><i class="bi bi-chat-text fs-1"></i></div>
                    <p class="text-secondary fw-bold mb-0">No comments found.</p>
                </div>`;
            document.getElementById('comment-pagination').innerHTML = '';
        }
    } catch (err) {
        console.error('Error loading comments:', err);
        tbody.innerHTML = `
            <div class="text-center py-4 text-danger">
                <i class="bi bi-exclamation-circle"></i> Failed to load comments.
            </div>`;
    }
}

// ==================== RENDER TABLE ROW ====================

function renderCommentRow(comment) {
    const name = escapeHtml(comment.commenter_name || 'Anonymous');
    const initial = name.charAt(0).toUpperCase();
    const email = escapeHtml(comment.commenter_email || '');
    const text = escapeHtml(truncate(comment.display_text || comment.original_text || '', 25));
    const blogTitle = escapeHtml(truncate(comment.blog_title || 'Unknown Post', 25));
    const date = comment.created_at ? formatDate(comment.created_at) : '';

    const statusBadge = getStatusBadge(comment.status);

    return `
    <div class="draft-row" id="comment-row-${comment.id}">
        <div class="col-commenter">
            <div class="commenter-info">
                <div class="commenter-avatar">${initial}</div>
                <div>
                    <div class="commenter-name">${name}</div>
                    <div class="commenter-date">${date}</div>
                </div>
            </div>
        </div>
        <div class="col-comment" title="${escapeHtml(comment.display_text || '')}">${text}</div>
        <div class="col-post">${blogTitle}</div>
        <div class="col-status">${statusBadge}</div>
        <div class="col-actions">
            <div class="dropdown">
                <button class="btn-dropdown-trigger" data-bs-toggle="dropdown">
                    <i class="bi bi-three-dots-vertical"></i>
                </button>
                <ul class="dropdown-menu dropdown-menu-end">
                    <li><a class="dropdown-item" href="#" onclick="openCommentModal('${comment.id}'); return false;">
                        <i class="bi bi-eye"></i> View Details
                    </a></li>
                    ${comment.status === 'published' ? `
                    <li><a class="dropdown-item" href="#" onclick="removeComment('${comment.id}'); return false;">
                        <i class="bi bi-eye-slash"></i> Remove from Site
                    </a></li>` : ''}
                    ${comment.status === 'removed' ? `
                    <li><a class="dropdown-item" href="#" onclick="restoreComment('${comment.id}'); return false;">
                        <i class="bi bi-arrow-counterclockwise"></i> Restore
                    </a></li>` : ''}
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-danger" href="#" onclick="deleteComment('${comment.id}'); return false;">
                        <i class="bi bi-trash"></i> Delete Permanently
                    </a></li>
                </ul>
            </div>
        </div>
    </div>`;
}

// ==================== BADGES ====================

function getAiBadge(action) {
    switch (action) {
        case 'approved':
            return '<span class="badge-ai badge-ai-approved"><i class="bi bi-check-lg"></i> Approved</span>';
        case 'edited':
            return '<span class="badge-ai badge-ai-edited"><i class="bi bi-pencil"></i> Edited</span>';
        case 'removed':
            return '<span class="badge-ai badge-ai-removed"><i class="bi bi-shield-x"></i> Removed</span>';
        default:
            return '<span class="badge-ai badge-ai-approved"><i class="bi bi-check-lg"></i> Approved</span>';
    }
}

function getStatusBadge(status) {
    switch (status) {
        case 'published':
            return '<span class="status-badge status-published"><i class="bi bi-circle-fill"></i> Published</span>';
        case 'removed':
            return '<span class="status-badge status-removed"><i class="bi bi-circle-fill"></i> Removed</span>';
        default:
            return '<span class="status-badge status-published"><i class="bi bi-circle-fill"></i> ' + escapeHtml(status || 'Unknown') + '</span>';
    }
}

// ==================== PAGINATION ====================

function renderPagination(total, page, perPage) {
    const container = document.getElementById('comment-pagination');
    const totalPages = Math.ceil(total / perPage);
    if (totalPages <= 1) { container.innerHTML = ''; return; }

    let html = '';
    html += `<button class="page-btn ${page <= 1 ? 'disabled' : ''}" onclick="goToPage(${page - 1})" ${page <= 1 ? 'disabled' : ''}>
        <i class="bi bi-chevron-left"></i>
    </button>`;

    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
            html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
        } else if (i === page - 2 || i === page + 2) {
            html += `<span class="page-dots">...</span>`;
        }
    }

    html += `<button class="page-btn ${page >= totalPages ? 'disabled' : ''}" onclick="goToPage(${page + 1})" ${page >= totalPages ? 'disabled' : ''}>
        <i class="bi bi-chevron-right"></i>
    </button>`;

    container.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadComments();
}

// ==================== VIEW/EDIT MODAL ====================

async function openCommentModal(commentId) {
    currentCommentId = commentId;

    // Reset to details tab
    document.querySelectorAll('.comment-modal-tabs .tab-item').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#commentModal .tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector('.tab-item[data-tab="details"]').classList.add('active');
    document.getElementById('tab-details').classList.add('active');

    try {
        const res = await fetch(`/api/comments/${commentId}`);
        const data = await res.json();

        if (data.success) {
            const c = data.comment;
            populateDetailsTab(c);
            populateModerationLog(c);
            populateEditTab(c);

            const modal = new bootstrap.Modal(document.getElementById('commentModal'));
            modal.show();
        } else {
            showToast({ type: 'error', title: 'Error', message: 'Failed to load comment details.', duration: 4000 });
        }
    } catch (err) {
        console.error('Error loading comment:', err);
        showToast({ type: 'error', title: 'Error', message: 'Failed to load comment details.', duration: 4000 });
    }
}

function populateDetailsTab(c) {
    const name = c.commenter_name || 'Anonymous';
    document.getElementById('modal-commenter-avatar').textContent = name.charAt(0).toUpperCase();
    document.getElementById('modal-commenter-name').textContent = name;
    document.getElementById('modal-commenter-email').textContent = c.commenter_email || '';
    document.getElementById('modal-blog-title').textContent = c.blog_title || 'Unknown Post';
    document.getElementById('modal-created-at').textContent = c.created_at ? formatDate(c.created_at) : '';
    document.getElementById('modal-original-text').textContent = c.original_text || '';
    document.getElementById('modal-display-text').textContent = c.display_text || '';

    // Status badge
    document.getElementById('modal-status-badge').innerHTML = getStatusBadge(c.status);

    // AI action chip — show as readable text
    const aiChip = document.getElementById('modal-ai-action-chip');
    const aiAction = c.ai_action || 'approved';
    const aiLabels = { approved: 'Approved', edited: 'Edited by AI', removed: 'Removed by AI' };
    aiChip.innerHTML = `<i class="bi bi-robot"></i> <span>${aiLabels[aiAction] || aiAction}</span>`;

    const moderatedSection = document.getElementById('modal-moderated-section');
    if (c.ai_action === 'edited' && c.moderated_text && c.moderated_text !== c.original_text) {
        moderatedSection.style.display = '';
        document.getElementById('modal-moderated-text').textContent = c.moderated_text;
    } else {
        moderatedSection.style.display = 'none';
    }

    // Hide save button on details tab
    document.getElementById('modal-save-edit').style.display = 'none';
}

function populateModerationLog(c) {
    const logEl = document.getElementById('modal-moderation-log');
    let html = '';

    // AI action entry
    html += `
    <div class="log-entry">
        <div class="log-icon log-icon-ai"><i class="bi bi-robot"></i></div>
        <div class="log-body">
            <div class="log-title">AI Moderation — ${getAiBadge(c.ai_action)}</div>
            ${c.ai_reason ? `<div class="log-reason">${escapeHtml(c.ai_reason)}</div>` : ''}
            <div class="log-date">${c.ai_moderated_at ? formatDate(c.ai_moderated_at) : 'At submission'}</div>
        </div>
    </div>`;

    // Admin edits
    if (c.admin_edits && c.admin_edits.length > 0) {
        c.admin_edits.forEach(edit => {
            html += `
            <div class="log-entry">
                <div class="log-icon log-icon-admin"><i class="bi bi-person-gear"></i></div>
                <div class="log-body">
                    <div class="log-title">Edited by <strong>${escapeHtml(edit.admin_name || 'Admin')}</strong></div>
                    ${edit.reason ? `<div class="log-reason">${escapeHtml(edit.reason)}</div>` : ''}
                    <div class="log-diff">
                        <div class="diff-old"><strong>Before:</strong> ${escapeHtml(truncate(edit.previous_text || '', 200))}</div>
                        <div class="diff-new"><strong>After:</strong> ${escapeHtml(truncate(edit.new_text || '', 200))}</div>
                    </div>
                    <div class="log-date">${edit.edited_at ? formatDate(edit.edited_at) : ''}</div>
                </div>
            </div>`;
        });
    }

    logEl.innerHTML = html;
}

function populateEditTab(c) {
    document.getElementById('modal-edit-text').value = c.display_text || '';
    document.getElementById('modal-edit-reason').value = '';
}

// ==================== SAVE EDIT ====================

async function saveCommentEdit() {
    const text = document.getElementById('modal-edit-text').value.trim();
    const reason = document.getElementById('modal-edit-reason').value.trim();

    if (!text) {
        showToast({ type: 'error', title: 'Error', message: 'Comment text cannot be empty.', duration: 3000 });
        return;
    }

    const btn = document.getElementById('modal-save-edit');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';

    try {
        const res = await fetch(`/api/comments/${currentCommentId}/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, reason })
        });
        const data = await res.json();

        if (data.success) {
            showToast({ type: 'success', title: 'Saved', message: 'Comment updated successfully.', duration: 3000 });
            bootstrap.Modal.getInstance(document.getElementById('commentModal')).hide();
            loadComments();
            refreshStats();
        } else {
            showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to save.', duration: 4000 });
        }
    } catch (err) {
        console.error('Save edit error:', err);
        showToast({ type: 'error', title: 'Error', message: 'Something went wrong.', duration: 4000 });
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check-lg"></i> Save Changes';
    }
}

// ==================== REMOVE / RESTORE ====================

async function removeComment(commentId) {
    try {
        const res = await fetch(`/api/comments/${commentId}/remove`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            showToast({ type: 'warning', title: 'Removed', message: 'Comment removed from public site.', duration: 3000 });
            animateRowOut(commentId);
            refreshStats();
        } else {
            showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to remove.', duration: 4000 });
        }
    } catch (err) {
        showToast({ type: 'error', title: 'Error', message: 'Something went wrong.', duration: 4000 });
    }
}

async function restoreComment(commentId) {
    try {
        const res = await fetch(`/api/comments/${commentId}/restore`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            showToast({ type: 'success', title: 'Restored', message: 'Comment restored to public site.', duration: 3000 });
            animateRowOut(commentId);
            refreshStats();
        } else {
            showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to restore.', duration: 4000 });
        }
    } catch (err) {
        showToast({ type: 'error', title: 'Error', message: 'Something went wrong.', duration: 4000 });
    }
}

// ==================== DELETE ====================

function deleteComment(commentId) {
    currentCommentId = commentId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

async function confirmDelete() {
    const btn = document.getElementById('confirm-delete-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Deleting...';

    try {
        const res = await fetch(`/api/comments/${currentCommentId}/delete`, { method: 'DELETE' });
        const data = await res.json();

        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            showToast({ type: 'success', title: 'Deleted', message: 'Comment permanently deleted.', duration: 3000 });
            animateRowOut(currentCommentId);
            refreshStats();
        } else {
            showToast({ type: 'error', title: 'Error', message: data.error || 'Failed to delete.', duration: 4000 });
        }
    } catch (err) {
        showToast({ type: 'error', title: 'Error', message: 'Something went wrong.', duration: 4000 });
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash"></i> Delete';
    }
}

// ==================== STATS REFRESH ====================

async function refreshStats() {
    try {
        const res = await fetch('/api/comments/stats');
        const data = await res.json();
        if (data.success && data.stats) {
            document.getElementById('stat-total').textContent = data.stats.total || 0;
            document.getElementById('stat-published').textContent = data.stats.published || 0;
            document.getElementById('stat-removed').textContent = data.stats.removed || 0;
        }
    } catch (err) {
        // Silently fail — stats refresh is non-critical
    }
}

// ==================== HELPERS ====================

function animateRowOut(commentId) {
    const row = document.getElementById('comment-row-' + commentId);
    if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(20px)';
        setTimeout(() => {
            row.remove();
            // Reload if no rows remain
            const tbody = document.getElementById('comments-table-body');
            if (!tbody.querySelector('.draft-row')) loadComments();
        }, 300);
    }
}

function truncate(str, max) {
    if (!str) return '';
    return str.length > max ? str.substring(0, max) + '...' : str;
}

function formatDate(dateStr) {
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
             + ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
        return '';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
