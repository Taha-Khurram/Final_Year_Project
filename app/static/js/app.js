/**
 * Scriptly AI - Main Application Logic
 * Global functions: showToast, showLoader, hideLoader
 */

// --------------------------------------------------------------------------
// DOM Elements
// --------------------------------------------------------------------------

const pageLoader = document.getElementById("page-loader");
const navProgress = document.getElementById("nav-progress");
const toastContainer = document.getElementById("toast-container");

// --------------------------------------------------------------------------
// Toast Notification System
// --------------------------------------------------------------------------

const showToast = (options) => {
    const { type = 'success', title, message, duration = 4000 } = options;

    const icons = {
        success: 'bi-check-circle-fill',
        error: 'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };

    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    toast.innerHTML = `
        <div class="toast-icon ${type}">
            <i class="bi ${icons[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.closest('.custom-toast').remove()">
            <i class="bi bi-x"></i>
        </button>
        <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
    `;

    if (toastContainer) {
        toastContainer.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto remove
        setTimeout(() => {
            toast.classList.add('hiding');
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, duration);
    }

    return toast;
};

// Expose globally
window.showToast = showToast;

// --------------------------------------------------------------------------
// Page Loader Functions
// --------------------------------------------------------------------------

const showLoader = () => {
    if (pageLoader) pageLoader.classList.remove("hidden");
    if (navProgress) navProgress.classList.add("loading");
};

const hideLoader = () => {
    if (pageLoader) pageLoader.classList.add("hidden");
    if (navProgress) {
        navProgress.classList.remove("loading");
        navProgress.style.width = "100%";
        setTimeout(() => { navProgress.style.width = "0%"; }, 300);
    }
};

// Expose globally
window.showLoader = showLoader;
window.hideLoader = hideLoader;

// --------------------------------------------------------------------------
// Page Load & Navigation Handling
// --------------------------------------------------------------------------

// Hide loader on page load
window.addEventListener("load", () => setTimeout(hideLoader, 200));

// Safety fallback: Force hide after 2.5 seconds if load event fails
setTimeout(hideLoader, 2500);

// Show loader on internal link click
document.addEventListener("click", (e) => {
    const link = e.target.closest("a");
    if (link && link.href &&
        !link.href.includes("#") &&
        !link.href.startsWith("javascript:") &&
        !link.href.startsWith("mailto:") &&
        link.target !== "_blank" &&
        !e.ctrlKey && !e.metaKey &&
        !link.hasAttribute('data-bs-toggle') &&
        !link.hasAttribute('download') &&
        !link.classList.contains('logout') &&
        !link.classList.contains('no-loader')) {

        // Only show loader for internal navigation
        const currentHost = window.location.host;
        const linkHost = new URL(link.href).host;

        if (currentHost === linkHost) {
            showLoader();
        }
    }
});

// Show loader on form submit (except AJAX forms)
document.addEventListener("submit", (e) => {
    if (!e.target.classList.contains('no-loader') &&
        !e.target.classList.contains('ajax-form')) {
        showLoader();
    }
});

// Hide loader on back/forward navigation
window.addEventListener("pageshow", (event) => {
    if (event.persisted) hideLoader();
});

// --------------------------------------------------------------------------
// Sidebar Active Link Handler
// --------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-menu a, .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});

// --------------------------------------------------------------------------
// Session Inactivity Timeout
// --------------------------------------------------------------------------

(function() {
    const TIMEOUT_MS = 15 * 60 * 1000;
    const WARN_MS = 2 * 60 * 1000;
    let timeoutTimer, warningTimer;

    function resetTimers() {
        clearTimeout(timeoutTimer);
        clearTimeout(warningTimer);

        warningTimer = setTimeout(() => {
            if (window.showToast) {
                showToast({
                    type: 'warning',
                    title: 'Session Expiring',
                    message: 'Your session will expire in 2 minutes due to inactivity.',
                    duration: 10000
                });
            }
        }, TIMEOUT_MS - WARN_MS);

        timeoutTimer = setTimeout(() => {
            window.location.href = '/login?expired=1';
        }, TIMEOUT_MS);
    }

    ['click', 'keydown', 'scroll', 'mousemove'].forEach(evt =>
        document.addEventListener(evt, resetTimers, { passive: true })
    );
    resetTimers();

    // Intercept fetch to handle 401 session_expired responses
    const _fetch = window.fetch;
    window.fetch = async function(...args) {
        const res = await _fetch.apply(this, args);
        if (res.status === 401) {
            try {
                const data = await res.clone().json();
                if (data.error === 'session_expired') {
                    window.location.href = data.redirect || '/login?expired=1';
                }
            } catch(e) {}
        }
        return res;
    };
})();
