/**
 * About Page JavaScript
 * Handles scroll animations and interactive elements
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== SCROLL ANIMATIONS ====================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all fade-in elements
    document.querySelectorAll('.fade-in-up').forEach(el => {
        observer.observe(el);
    });

    // ==================== VALUE CARDS STAGGER ANIMATION ====================
    const valueCards = document.querySelectorAll('.about-value-card');
    valueCards.forEach((card, index) => {
        card.style.transitionDelay = `${index * 0.1}s`;
    });

    // ==================== STAT ITEMS STAGGER ANIMATION ====================
    const statItems = document.querySelectorAll('.about-stat-item');
    statItems.forEach((item, index) => {
        item.style.transitionDelay = `${index * 0.1}s`;
    });

    // ==================== STAT COUNTER ANIMATION ====================
    const statNumbers = document.querySelectorAll('.about-stat-number');
    const statsSection = document.querySelector('.about-stats');

    if (statsSection && statNumbers.length > 0) {
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateStats();
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        statsObserver.observe(statsSection);
    }

    function animateStats() {
        statNumbers.forEach(stat => {
            const text = stat.textContent;
            const hasPlus = text.includes('+');
            const hasK = text.includes('K');
            const hasSlash = text.includes('/');

            // Skip non-numeric stats like "24/7"
            if (hasSlash) return;

            // Extract the numeric value
            let target = parseInt(text.replace(/[^0-9]/g, ''));
            if (isNaN(target)) return;

            let current = 0;
            const increment = target / 40;
            const duration = 1200;
            const stepTime = duration / 40;

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }

                let displayValue = Math.floor(current);
                if (hasK) {
                    displayValue = displayValue + 'K';
                }
                if (hasPlus) {
                    displayValue = displayValue + '+';
                }

                stat.textContent = displayValue;
            }, stepTime);
        });
    }
});
