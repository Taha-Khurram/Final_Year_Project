// User Management JS - Robust Version
console.log("� Users JS: Script loaded.");

// --- Helper Functions ---
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Main function to fetch and render the user list.
 */
async function loadUsers() {
    console.log("🔄 Users JS: loadUsers() triggered.");
    const usersList = document.getElementById('usersList');
    const noUsers = document.getElementById('noUsers');

    if (!usersList) {
        console.error("❌ Users JS: 'usersList' element not found.");
        return;
    }

    // Immediately update UI to show activity
    usersList.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary opacity-50 mb-3" role="status"></div>
            <p class="text-secondary fw-medium">Syncing with server...</p>
        </div>
    `;

    try {
        console.log("📡 Users JS: Fetching /users/list...");
        const response = await fetch('/users/list');

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("📥 Users JS: Data received:", data);

        if (!data.success) {
            throw new Error(data.error || "Failed to fetch users.");
        }

        const users = data.users || [];
        console.log(`✨ Users JS: Sync complete. Found ${users.length} users.`);

        if (users.length === 0) {
            usersList.innerHTML = '';
            if (noUsers) noUsers.classList.remove('d-none');
            return;
        }

        if (noUsers) noUsers.classList.add('d-none');

        // Render rows
        usersList.innerHTML = users.map(user => {
            if (!user) return '';
            const uid = user.uid || 'unknown';
            const name = (user.name || user.username || 'User').trim();
            const email = (user.email || 'no-email@scriptly.ai').trim();
            const role = (user.role || 'editor').toLowerCase().trim();
            const initials = (name === 'User' ? email[0] : name.substring(0, 2)).toUpperCase();
            const roleClass = role === 'admin' ? 'badge-admin' : 'badge-editor';

            return `
                <div class="user-row animate-fade-up">
                    <div class="col-username d-flex align-items-center gap-3">
                        <div class="footer-avatar shadow-sm" style="width: 36px; height: 36px; font-size: 0.8rem; border-radius: 10px;">
                            ${initials}
                        </div>
                        <span class="fw-bold">${escapeHtml(name)}</span>
                    </div>
                    <div class="col-email text-secondary">${escapeHtml(email)}</div>
                    <div class="col-role">
                        <span class="badge-role ${roleClass}">${role.toUpperCase()}</span>
                    </div>
                    <div class="col-actions">
                        <button class="btn btn-sm btn-light rounded-circle shadow-sm" 
                            onclick="openEditRole('${uid}', '${escapeHtml(name)}', '${role}')"
                            style="width: 32px; height: 32px; padding: 0;">
                            <i class="bi bi-pencil-square text-primary"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('❌ Users JS: loadUsers Error:', error);
        usersList.innerHTML = `
            <div class="p-5 text-center bg-white rounded border">
                <div class="text-danger mb-2"><i class="bi bi-exclamation-triangle-fill fs-2"></i></div>
                <p class="text-secondary fw-bold">Sync Error</p>
                <p class="small text-muted mb-3">${error.message}</p>
                <button class="btn btn-sm btn-primary rounded-pill px-4" onclick="loadUsers()">Retry Sync</button>
            </div>
        `;
    }
}

function openEditRole(uid, username, currentRole) {
    console.log(`✏️ Users JS: Opening edit role for ${username}`);
    const userIdInput = document.getElementById('editUserId');
    const usernameInput = document.getElementById('editUsername');
    const roleInput = document.getElementById('editRole');

    if (userIdInput) userIdInput.value = uid;
    if (usernameInput) usernameInput.value = username;
    if (roleInput) roleInput.value = currentRole.toLowerCase();

    const modalEl = document.getElementById('editRoleModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
        const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modalInstance.show();
    }
}

// --- Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Users JS: DOM Content Loaded. Initializing handlers...");

    // Initial Load
    loadUsers();

    const addUserForm = document.getElementById('createUserForm');
    const editRoleForm = document.getElementById('editRoleForm');

    if (addUserForm) {
        addUserForm.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log("🚀 Users JS: Creating user...");
            if (window.showLoader) window.showLoader();

            const data = Object.fromEntries(new FormData(addUserForm).entries());
            fetch('/users/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
                .then(res => res.json())
                .then(result => {
                    if (result.success) {
                        const modalEl = document.getElementById('addUserModal');
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.hide();
                        addUserForm.reset();
                        loadUsers();
                    } else {
                        alert('Error: ' + result.error);
                    }
                })
                .catch(err => {
                    console.error("❌ Users JS: Create error", err);
                    alert("Connection failed.");
                })
                .finally(() => { if (window.hideLoader) window.hideLoader(); });
        });
    }

    if (editRoleForm) {
        editRoleForm.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log("🚀 Users JS: Updating role...");
            if (window.showLoader) window.showLoader();

            const userId = document.getElementById('editUserId').value;
            const role = document.getElementById('editRole').value;

            fetch('/users/update-role', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId, role })
            })
                .then(res => res.json())
                .then(result => {
                    if (result.success) {
                        const modalEl = document.getElementById('editRoleModal');
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.hide();
                        loadUsers();
                    } else {
                        alert('Error: ' + result.error);
                    }
                })
                .catch(err => console.error("❌ Users JS: Update error", err))
                .finally(() => { if (window.hideLoader) window.hideLoader(); });
        });
    }
});

// Global Error Catch to help debug
window.onerror = function (msg, url, lineNo, columnNo, error) {
    console.error(`🔴 Global Script Error: ${msg}\nUrl: ${url}\nLine: ${lineNo}\nCol: ${columnNo}\nError:`, error);
    return false;
};