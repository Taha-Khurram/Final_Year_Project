/**
 * Scroll Animations
 * Uses Intersection Observer to trigger animations when elements enter viewport
 */

(function() {
    'use strict';

    // Configuration
    const config = {
        threshold: 0.15,        // Trigger when 15% of element is visible
        rootMargin: '0px 0px -50px 0px',  // Trigger slightly before element enters
        once: true              // Only animate once per element
    };

    // Elements to auto-animate (applied automatically)
    const autoAnimateSelectors = [
        // Hero sections
        '.site-hero .hero-content',
        '.site-hero .hero-illustration svg',
        '.about-hero .about-hero-content',
        '.about-hero .about-hero-illustration svg',
        '.contact-hero .contact-hero-content',
        '.contact-hero .contact-hero-illustration svg',
        '.blog-hero .blog-hero-content',
        '.blog-hero .blog-hero-illustration svg',

        // Cards and sections
        '.featured-card',
        '.blog-card',
        '.value-card',
        '.faq-card',
        '.sidebar-card',
        '.story-card',
        '.contact-form-card',

        // Stats
        '.stats-section',
        '.hero-stats',
        '.blog-hero-stats',

        // Other sections
        '.newsletter-section',
        '.cta-section',
        '.empty-state',

        // Section headers
        '.section-header',
        '.section-title'
    ];

    // Auto-stagger selectors (grids that should stagger their children)
    const autoStaggerSelectors = [
        '.featured-grid',
        '.blog-grid',
        '.values-grid',
        '.faq-grid',
        '.stats-grid',
        '.category-filter'
    ];

    /**
     * Initialize scroll animations
     */
    function init() {
        // Check for reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            // Show all elements immediately
            document.querySelectorAll('[data-animate], [data-animate-stagger]').forEach(el => {
                el.classList.add('animated');
            });
            return;
        }

        // Apply auto-animations
        applyAutoAnimations();

        // Create observer
        const observer = createObserver();

        // Observe all animated elements
        observeElements(observer);

        // Initialize parallax if any
        initParallax();

        // Animate hero illustrations on load
        animateHeroOnLoad();
    }

    /**
     * Apply automatic animation attributes to common elements
     */
    function applyAutoAnimations() {
        // Apply fade-up to common selectors
        autoAnimateSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach((el, index) => {
                if (!el.hasAttribute('data-animate') && !el.closest('[data-animate-stagger]')) {
                    el.setAttribute('data-animate', 'fade-up');

                    // Add slight delay based on position in page
                    if (index > 0 && index < 8) {
                        el.setAttribute('data-animate-delay', String(index * 100));
                    }
                }
            });
        });

        // Apply stagger to grids
        autoStaggerSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                if (!el.hasAttribute('data-animate-stagger')) {
                    el.setAttribute('data-animate-stagger', '');
                }
            });
        });
    }

    /**
     * Create Intersection Observer instance
     */
    function createObserver() {
        return new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;

                    // Add animated class
                    target.classList.add('animated');

                    // Animate counters if present
                    if (target.querySelector('[data-counter]')) {
                        animateCounters(target);
                    }

                    // Unobserve if only animating once
                    if (config.once) {
                        observer.unobserve(target);
                    }
                }
            });
        }, {
            threshold: config.threshold,
            rootMargin: config.rootMargin
        });
    }

    /**
     * Observe all elements with animation attributes
     */
    function observeElements(observer) {
        // Elements with data-animate
        document.querySelectorAll('[data-animate]').forEach(el => {
            observer.observe(el);
        });

        // Elements with data-animate-stagger
        document.querySelectorAll('[data-animate-stagger]').forEach(el => {
            observer.observe(el);
        });

        // SVG illustrations
        document.querySelectorAll(
            '.hero-illustration svg, ' +
            '.about-hero-illustration svg, ' +
            '.contact-hero-illustration svg, ' +
            '.blog-hero-illustration svg'
        ).forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Animate counter numbers
     */
    function animateCounters(container) {
        container.querySelectorAll('[data-counter]').forEach(counter => {
            const target = parseInt(counter.getAttribute('data-counter') || counter.textContent, 10);
            const duration = 1500;
            const start = 0;
            const startTime = performance.now();

            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Easing function (ease-out)
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(start + (target - start) * easeOut);

                counter.textContent = current.toLocaleString();

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target.toLocaleString();
                }
            }

            requestAnimationFrame(updateCounter);
        });
    }

    /**
     * Initialize parallax scrolling
     */
    function initParallax() {
        const parallaxElements = document.querySelectorAll('[data-parallax]');

        if (parallaxElements.length === 0) return;

        let ticking = false;

        function updateParallax() {
            const scrollY = window.pageYOffset;

            parallaxElements.forEach(el => {
                const speed = parseFloat(el.getAttribute('data-parallax')) || 0.5;
                const rect = el.getBoundingClientRect();
                const offsetTop = rect.top + scrollY;
                const distance = scrollY - offsetTop;

                if (rect.top < window.innerHeight && rect.bottom > 0) {
                    el.style.transform = `translateY(${distance * speed}px)`;
                }
            });

            ticking = false;
        }

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateParallax);
                ticking = true;
            }
        }, { passive: true });
    }

    /**
     * Animate hero illustrations immediately on page load
     */
    function animateHeroOnLoad() {
        // Wait for DOM to be ready
        requestAnimationFrame(() => {
            // Slight delay for page to settle
            setTimeout(() => {
                // Animate hero content
                const heroContent = document.querySelector(
                    '.site-hero .hero-content, ' +
                    '.about-hero .about-hero-content, ' +
                    '.contact-hero .contact-hero-content, ' +
                    '.blog-hero .blog-hero-content'
                );
                if (heroContent) {
                    heroContent.classList.add('animated');
                }

                // Animate hero illustration after content
                setTimeout(() => {
                    const heroSvg = document.querySelector(
                        '.hero-illustration svg, ' +
                        '.about-hero-illustration svg, ' +
                        '.contact-hero-illustration svg, ' +
                        '.blog-hero-illustration svg'
                    );
                    if (heroSvg) {
                        heroSvg.classList.add('animated');
                    }
                }, 200);

                // Animate hero stats
                setTimeout(() => {
                    const heroStats = document.querySelector('.hero-stats, .blog-hero-stats');
                    if (heroStats) {
                        heroStats.classList.add('animated');
                    }
                }, 400);
            }, 100);
        });
    }

    /**
     * Utility: Check if element is in viewport
     */
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top < window.innerHeight &&
            rect.bottom > 0 &&
            rect.left < window.innerWidth &&
            rect.right > 0
        );
    }

    /**
     * Utility: Add animation to element
     */
    window.addScrollAnimation = function(element, animationType = 'fade-up', delay = 0) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.setAttribute('data-animate', animationType);
            if (delay) {
                element.setAttribute('data-animate-delay', String(delay));
            }
        }
    };

    /**
     * Utility: Refresh animations (useful for dynamically added content)
     */
    window.refreshScrollAnimations = function() {
        applyAutoAnimations();
        const observer = createObserver();
        observeElements(observer);
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
