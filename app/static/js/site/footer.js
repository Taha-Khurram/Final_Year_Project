/**
 * Site Footer JavaScript
 * Handles newsletter form submission in the footer
 */

document.addEventListener('DOMContentLoaded', function() {
    // Footer Newsletter Form
    const footerForm = document.getElementById('footer-newsletter-form');
    if (footerForm) {
        footerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const subscribeUrl = footerForm.dataset.subscribeUrl;
            if (subscribeUrl) {
                handleNewsletterSubmit(this, subscribeUrl);
            }
        });
    }
});
