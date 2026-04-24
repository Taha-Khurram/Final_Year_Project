/**
 * Blog Page JavaScript
 * Handles filtering, sorting, view toggle, and sidebar interactions
 */

let subscribeUrl = '';

function initBlogPage(url) {
    subscribeUrl = url;
}

document.addEventListener('DOMContentLoaded', function() {
    const blogGrid = document.getElementById('blog-grid');
    const sortSelect = document.getElementById('sort-select');
    const viewButtons = document.querySelectorAll('.view-btn');
    const sidebarSubscribeBtn = document.getElementById('sidebar-subscribe-btn');

    // ==================== SORT FUNCTIONALITY ====================
    if (sortSelect && blogGrid) {
        sortSelect.addEventListener('change', function() {
            const cards = Array.from(blogGrid.querySelectorAll('.blog-card'));

            cards.sort((a, b) => {
                switch(this.value) {
                    case 'oldest':
                        return parseFloat(a.dataset.date) - parseFloat(b.dataset.date);
                    case 'title':
                        return a.dataset.title.localeCompare(b.dataset.title);
                    default: // latest
                        return parseFloat(b.dataset.date) - parseFloat(a.dataset.date);
                }
            });

            // Re-append sorted cards with animation
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(10px)';

                setTimeout(() => {
                    blogGrid.appendChild(card);
                    requestAnimationFrame(() => {
                        card.style.transition = 'all 0.3s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    });
                }, index * 50);
            });
        });
    }

    // ==================== VIEW TOGGLE ====================
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.dataset.view;

            // Update active button
            viewButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Toggle grid view class
            if (blogGrid) {
                if (view === 'list') {
                    blogGrid.classList.add('list-view');
                } else {
                    blogGrid.classList.remove('list-view');
                }

                // Save preference
                localStorage.setItem('blog-view', view);
            }
        });
    });

    // Restore view preference
    const savedView = localStorage.getItem('blog-view');
    if (savedView && blogGrid) {
        const savedBtn = document.querySelector(`[data-view="${savedView}"]`);
        if (savedBtn) {
            savedBtn.click();
        }
    }

    // ==================== SIDEBAR SUBSCRIBE ====================
    if (sidebarSubscribeBtn) {
        sidebarSubscribeBtn.addEventListener('click', function() {
            // Open subscribe modal from header
            const subscribeModal = document.getElementById('subscribe-modal');
            if (subscribeModal) {
                subscribeModal.classList.add('active');
                document.body.style.overflow = 'hidden';
                const emailInput = subscribeModal.querySelector('input[type="email"]');
                if (emailInput) {
                    setTimeout(() => emailInput.focus(), 100);
                }
            }
        });
    }

    // ==================== SCROLL ANIMATIONS ====================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -30px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe blog cards for scroll animation
    document.querySelectorAll('.blog-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `all 0.4s ease ${index * 0.05}s`;
        observer.observe(card);
    });

    // ==================== FILTER TABS ACTIVE STATE ====================
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Add loading state
            if (blogGrid) {
                blogGrid.style.opacity = '0.5';
            }
        });
    });
});
