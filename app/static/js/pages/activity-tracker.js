/**
 * Scriptly AI - Activity Tracker
 * Records every click and action on the admin dashboard to Google Sheets
 */

(function() {
    'use strict';

    const FLUSH_INTERVAL = 5000;
    const MAX_BATCH_SIZE = 25;
    let eventQueue = [];
    let flushTimer = null;
    let isTracking = true;

    function getElementDescriptor(el) {
        if (!el || !el.tagName) return '';

        const tag = el.tagName.toLowerCase();
        const text = (el.textContent || '').trim().substring(0, 80);
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className && typeof el.className === 'string'
            ? '.' + el.className.split(' ').filter(c => c).slice(0, 3).join('.')
            : '';
        const href = el.getAttribute('href') || '';
        const dataAction = el.getAttribute('data-action') || '';
        const ariaLabel = el.getAttribute('aria-label') || '';
        const title = el.getAttribute('title') || '';

        let descriptor = tag + id + classes;
        if (text && text.length < 50) descriptor += ` "${text}"`;
        if (href) descriptor += ` [href=${href}]`;
        if (dataAction) descriptor += ` [action=${dataAction}]`;
        if (ariaLabel) descriptor += ` [aria=${ariaLabel}]`;
        if (title) descriptor += ` [title=${title}]`;

        return descriptor.substring(0, 200);
    }

    function getActionType(el) {
        if (!el) return 'click';
        const tag = el.tagName.toLowerCase();

        if (tag === 'a') return 'navigation';
        if (tag === 'button' || el.getAttribute('role') === 'button') return 'button_click';
        if (tag === 'input' || tag === 'select' || tag === 'textarea') return 'form_interaction';
        if (el.classList && el.classList.contains('settings-tab')) return 'tab_switch';
        if (el.classList && el.classList.contains('nav-link')) return 'navigation';
        if (el.closest && el.closest('.modal')) return 'modal_interaction';
        if (el.closest && el.closest('.dropdown-menu')) return 'dropdown_select';

        return 'click';
    }

    function getActionDescription(el) {
        if (!el) return '';
        const tag = el.tagName.toLowerCase();

        if (tag === 'a') {
            const text = (el.textContent || '').trim().substring(0, 50);
            return `Navigated: ${text || el.getAttribute('href') || 'link'}`;
        }
        if (tag === 'button' || el.getAttribute('role') === 'button') {
            const text = (el.textContent || '').trim().substring(0, 50);
            return `Clicked: ${text || 'button'}`;
        }
        if (el.classList && el.classList.contains('settings-tab')) {
            return `Switched tab: ${el.dataset.tab || el.textContent.trim()}`;
        }
        if (tag === 'input' && el.type === 'submit') {
            return `Submitted: ${el.value || 'form'}`;
        }

        const text = (el.textContent || '').trim().substring(0, 50);
        return `Clicked: ${text || el.tagName}`;
    }

    function trackEvent(eventData) {
        if (!isTracking) return;

        eventData.timestamp = new Date().toISOString();
        eventData.page = window.location.pathname;
        eventQueue.push(eventData);

        if (eventQueue.length >= MAX_BATCH_SIZE) {
            flushEvents();
        }
    }

    function flushEvents() {
        if (eventQueue.length === 0) return;

        const events = eventQueue.splice(0, MAX_BATCH_SIZE);

        fetch('/api/track-activity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ events: events })
        }).catch(function(err) {
            console.debug('Activity tracking flush failed:', err.message);
        });
    }

    // Track all clicks via event delegation
    document.addEventListener('click', function(e) {
        if (!isTracking) return;

        const el = e.target.closest('a, button, [role="button"], .settings-tab, .nav-link, input[type="submit"], .dropdown-item, .btn');
        if (!el) {
            // Still track raw clicks on other elements if they seem meaningful
            if (e.target.closest('.sidebar, .card, .modal, .table')) {
                trackEvent({
                    action_type: 'click',
                    action: `Clicked: ${(e.target.textContent || '').trim().substring(0, 50) || e.target.tagName}`,
                    element: getElementDescriptor(e.target),
                    details: ''
                });
            }
            return;
        }

        trackEvent({
            action_type: getActionType(el),
            action: getActionDescription(el),
            element: getElementDescriptor(el),
            details: ''
        });
    }, true);

    // Track page visits
    trackEvent({
        action_type: 'page_visit',
        action: `Visited: ${document.title || window.location.pathname}`,
        element: '',
        details: document.referrer ? `From: ${document.referrer}` : 'Direct'
    });

    // Track form submissions
    document.addEventListener('submit', function(e) {
        if (!isTracking) return;
        const form = e.target;
        const formId = form.id || form.action || 'unknown-form';
        trackEvent({
            action_type: 'form_submit',
            action: `Submitted form: ${formId}`,
            element: `form#${form.id || ''}.${(form.className || '').split(' ')[0] || ''}`,
            details: `Method: ${form.method || 'GET'}`
        });
    }, true);

    // Track PJAX navigation (app uses PJAX for page transitions)
    document.addEventListener('pjax:complete', function() {
        trackEvent({
            action_type: 'page_visit',
            action: `Navigated: ${document.title || window.location.pathname}`,
            element: '',
            details: 'PJAX transition'
        });
    });

    // Periodic flush
    flushTimer = setInterval(flushEvents, FLUSH_INTERVAL);

    // Flush on page unload
    window.addEventListener('beforeunload', function() {
        if (eventQueue.length > 0) {
            const events = eventQueue.splice(0);
            navigator.sendBeacon('/api/track-activity', JSON.stringify({ events: events }));
        }
    });

    // Expose control methods for enabling/disabling
    window.ScriptlyTracker = {
        enable: function() { isTracking = true; },
        disable: function() { isTracking = false; },
        flush: flushEvents,
        isEnabled: function() { return isTracking; }
    };

})();
