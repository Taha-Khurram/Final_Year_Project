/**
 * Lightweight Scroll Animations
 */
(function() {
    'use strict';

    // Check for reduced motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.querySelectorAll('[data-animate], [data-animate-stagger]').forEach(el => {
            el.classList.add('animated');
        });
        return;
    }

    // Simple observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px 50px 0px'
    });

    // Observe elements
    function init() {
        // Manual data-animate elements
        document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
        document.querySelectorAll('[data-animate-stagger]').forEach(el => observer.observe(el));

        // Hero SVGs - animate immediately
        setTimeout(() => {
            document.querySelectorAll(
                '.hero-illustration svg, .about-hero-illustration svg, ' +
                '.contact-hero-illustration svg, .blog-hero-illustration svg'
            ).forEach(svg => svg.classList.add('animated'));
        }, 100);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
