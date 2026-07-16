/**
 * Site interaction & scroll animations
 * - Scroll-reveal (IntersectionObserver)
 * - Reading scroll-progress bar
 * - Cursor spotlight on cards
 * - Count-up statistics
 * All features degrade gracefully and honour prefers-reduced-motion.
 */
(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------------------------------------------------------------------
       1. Scroll reveal
       Fail-safe by design: content is NEVER left stuck at opacity:0.
       - threshold 0 => fires on the first intersecting pixel, so containers
         taller than the viewport (long articles, big grids) still reveal.
       - a timeout force-reveals anything the observer somehow missed.
    --------------------------------------------------------------------- */
    function reveal(el) { el.classList.add('animated'); }

    function initReveal() {
        var targets = document.querySelectorAll('[data-animate], [data-animate-stagger]');

        if (reduceMotion || !('IntersectionObserver' in window)) {
            targets.forEach(reveal);
        } else {
            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        reveal(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0, rootMargin: '0px 0px -40px 0px' });

            targets.forEach(function (el) { observer.observe(el); });

            // Safety net: whatever hasn't revealed within 1.6s, reveal now.
            // Guards against tall elements, flaky observers, or layout timing.
            setTimeout(function () { targets.forEach(reveal); }, 1600);
        }

        // Legacy hero SVGs animate in immediately
        setTimeout(function () {
            document.querySelectorAll(
                '.hero-illustration svg, .about-hero-illustration svg, ' +
                '.contact-hero-illustration svg, .blog-hero-illustration svg'
            ).forEach(function (svg) { svg.classList.add('animated'); });
        }, 100);
    }

    /* ---------------------------------------------------------------------
       2. Reading scroll-progress bar
    --------------------------------------------------------------------- */
    function initScrollProgress() {
        if (reduceMotion) return;

        var bar = document.createElement('div');
        bar.className = 'scroll-progress';
        document.body.appendChild(bar);

        var ticking = false;
        function update() {
            var doc = document.documentElement;
            var scrollable = doc.scrollHeight - doc.clientHeight;
            var pct = scrollable > 0 ? (doc.scrollTop / scrollable) * 100 : 0;
            bar.style.width = pct + '%';
            ticking = false;
        }
        window.addEventListener('scroll', function () {
            if (!ticking) { window.requestAnimationFrame(update); ticking = true; }
        }, { passive: true });
        update();
    }

    /* ---------------------------------------------------------------------
       3. Cursor spotlight on cards
    --------------------------------------------------------------------- */
    function initSpotlight() {
        if (reduceMotion || window.matchMedia('(hover: none)').matches) return;

        var cards = document.querySelectorAll(
            '[data-spotlight], .latest-inline-card, .blog-card, .featured-card, .stat-card'
        );

        cards.forEach(function (card) {
            card.addEventListener('pointermove', function (e) {
                var rect = card.getBoundingClientRect();
                card.style.setProperty('--spot-x', ((e.clientX - rect.left) / rect.width * 100) + '%');
                card.style.setProperty('--spot-y', ((e.clientY - rect.top) / rect.height * 100) + '%');
            });
        });
    }

    /* ---------------------------------------------------------------------
       4. Count-up statistics
       Targets explicit [data-count] plus common stat elements. Parses a
       leading number and preserves any suffix (e.g. "+", "k", "%").
    --------------------------------------------------------------------- */
    function initCountUp() {
        var els = document.querySelectorAll(
            '[data-count], .about-platform-stat strong, .hero-stat-number, .stat-number'
        );
        if (!els.length) return;

        function run(el) {
            var raw = (el.getAttribute('data-count') || el.textContent || '').trim();
            var match = raw.match(/([\d,.]+)/);
            if (!match) return;

            var target = parseFloat(match[1].replace(/,/g, ''));
            if (isNaN(target)) return;

            var prefix = raw.slice(0, match.index);
            var suffix = raw.slice(match.index + match[1].length);
            var isFloat = match[1].indexOf('.') !== -1;

            if (reduceMotion) { el.textContent = prefix + match[1] + suffix; return; }

            var duration = 1200;
            var startTime = null;
            function step(ts) {
                if (startTime === null) startTime = ts;
                var progress = Math.min((ts - startTime) / duration, 1);
                var eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
                var value = target * eased;
                el.textContent = prefix + (isFloat ? value.toFixed(1) : Math.round(value).toLocaleString()) + suffix;
                if (progress < 1) window.requestAnimationFrame(step);
            }
            window.requestAnimationFrame(step);
        }

        if (!('IntersectionObserver' in window)) { els.forEach(run); return; }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    run(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.6 });

        els.forEach(function (el) { observer.observe(el); });
    }

    /* --------------------------------------------------------------------- */
    function init() {
        initReveal();
        initScrollProgress();
        initSpotlight();
        initCountUp();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
