/**
 * Site Header JavaScript
 * Handles mobile menu, search, and subscribe modal
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== MOBILE MENU ====================
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const mobileNav = document.querySelector('.mobile-nav');

    if (mobileToggle && mobileNav) {
        mobileToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            mobileNav.classList.toggle('active');
        });

        // Close mobile menu when clicking a link
        document.querySelectorAll('.mobile-nav a').forEach(link => {
            link.addEventListener('click', () => {
                mobileToggle.classList.remove('active');
                mobileNav.classList.remove('active');
            });
        });
    }

    // ==================== SEARCH FUNCTIONALITY ====================
    const searchInputs = document.querySelectorAll('#header-search-input, .mobile-search input');

    searchInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = this.value.trim();
                const searchUrl = this.dataset.searchUrl;
                if (query && searchUrl) {
                    window.location.href = `${searchUrl}?search=${encodeURIComponent(query)}`;
                }
            }
        });
    });

    // ==================== SUBSCRIBE MODAL ====================
    const subscribeModal = document.getElementById('subscribe-modal');
    const subscribeModalClose = document.getElementById('subscribe-modal-close');
    const headerSubscribeBtn = document.getElementById('header-subscribe-btn');
    const mobileSubscribeBtn = document.getElementById('mobile-subscribe-btn');
    const subscribeForm = document.getElementById('subscribe-modal-form');

    function openSubscribeModal() {
        if (subscribeModal) {
            subscribeModal.classList.add('active');
            document.body.style.overflow = 'hidden';
            // Focus the email input
            const emailInput = subscribeModal.querySelector('input[type="email"]');
            if (emailInput) {
                setTimeout(() => emailInput.focus(), 100);
            }
        }
    }

    function closeSubscribeModal() {
        if (subscribeModal) {
            subscribeModal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Open modal buttons
    if (headerSubscribeBtn) {
        headerSubscribeBtn.addEventListener('click', openSubscribeModal);
    }

    if (mobileSubscribeBtn) {
        mobileSubscribeBtn.addEventListener('click', function() {
            // Close mobile menu first
            if (mobileToggle) mobileToggle.classList.remove('active');
            if (mobileNav) mobileNav.classList.remove('active');
            openSubscribeModal();
        });
    }

    // Close modal
    if (subscribeModalClose) {
        subscribeModalClose.addEventListener('click', closeSubscribeModal);
    }

    // Close on overlay click
    if (subscribeModal) {
        subscribeModal.addEventListener('click', function(e) {
            if (e.target === this) closeSubscribeModal();
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && subscribeModal && subscribeModal.classList.contains('active')) {
            closeSubscribeModal();
        }
    });

    // Subscribe form submission
    if (subscribeForm) {
        subscribeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const subscribeUrl = this.dataset.subscribeUrl;
            if (subscribeUrl && typeof handleNewsletterSubmit === 'function') {
                await handleNewsletterSubmit(this, subscribeUrl);
                closeSubscribeModal();
            }
        });
    }
});
