/**
 * Semantic Search Agent
 * Handles the floating search button and modal interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const trigger = document.getElementById('search-agent-trigger');
    const overlay = document.getElementById('search-agent-overlay');
    const modal = document.getElementById('search-agent-modal');
    const closeBtn = document.getElementById('search-agent-close');
    const input = document.getElementById('search-agent-input');
    const searchUrl = input?.dataset.searchUrl;

    // States
    const initialState = document.getElementById('search-agent-initial');
    const loadingState = document.getElementById('search-agent-loading');
    const emptyState = document.getElementById('search-agent-empty');
    const resultsList = document.getElementById('search-agent-list');
    const resultsCount = document.getElementById('search-results-count');

    let debounceTimer;

    // Open modal
    function openModal() {
        overlay?.classList.add('active');
        modal?.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(() => input?.focus(), 300);
    }

    // Close modal
    function closeModal() {
        overlay?.classList.remove('active');
        modal?.classList.remove('active');
        document.body.style.overflow = '';
        resetStates();
    }

    // Reset to initial state
    function resetStates() {
        if (input) input.value = '';
        initialState?.classList.remove('hidden');
        loadingState?.classList.remove('active');
        emptyState?.classList.remove('active');
        resultsList?.classList.remove('active');
        if (resultsCount) resultsCount.textContent = '';
        if (resultsList) resultsList.innerHTML = '';
    }

    // Show loading state
    function showLoading() {
        initialState?.classList.add('hidden');
        loadingState?.classList.add('active');
        emptyState?.classList.remove('active');
        resultsList?.classList.remove('active');
    }

    // Show empty state
    function showEmpty(query) {
        loadingState?.classList.remove('active');
        emptyState?.classList.add('active');
        resultsList?.classList.remove('active');
        const emptyTitle = emptyState?.querySelector('h4');
        if (emptyTitle) {
            emptyTitle.textContent = `No results for "${query}"`;
        }
    }

    // Show results
    function showResults(results, query) {
        loadingState?.classList.remove('active');
        emptyState?.classList.remove('active');

        if (!results || results.length === 0) {
            showEmpty(query);
            return;
        }

        resultsList?.classList.add('active');
        if (resultsCount) {
            resultsCount.textContent = `Found ${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"`;
        }

        if (resultsList) {
            resultsList.innerHTML = results.map(result => `
                <a href="${result.url}" class="search-result-item">
                    ${result.cover_image
                        ? `<img src="${result.cover_image}" alt="" class="search-result-image">`
                        : `<div class="search-result-image"></div>`
                    }
                    <div class="search-result-content">
                        <h4 class="search-result-title">${escapeHtml(result.title)}</h4>
                        ${result.match_reason && result.match_reason.length > 0
                            ? `<p class="search-result-reason">"${escapeHtml(result.match_reason)}"</p>`
                            : `<p class="search-result-excerpt">${escapeHtml(result.excerpt || '')}</p>`
                        }
                        <div class="search-result-meta">
                            ${result.category
                                ? `<span class="search-result-category">${escapeHtml(result.category)}</span>`
                                : ''
                            }
                            <span class="search-result-score">${Math.round(result.score * 100)}% match</span>
                        </div>
                    </div>
                </a>
            `).join('');
        }
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Perform search
    async function performSearch(query) {
        if (!query || query.length < 2 || !searchUrl) {
            if (query.length === 0) {
                initialState?.classList.remove('hidden');
                loadingState?.classList.remove('active');
                emptyState?.classList.remove('active');
                resultsList?.classList.remove('active');
            }
            return;
        }

        showLoading();

        try {
            const response = await fetch(searchUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (data.success) {
                showResults(data.results, query);
            } else {
                showEmpty(query);
            }
        } catch (error) {
            console.error('Search error:', error);
            showEmpty(query);
        }
    }

    // Event listeners
    trigger?.addEventListener('click', openModal);

    closeBtn?.addEventListener('click', closeModal);

    overlay?.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeModal();
        }
    });

    // Escape key to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal?.classList.contains('active')) {
            closeModal();
        }
    });

    // Input handler with debounce
    input?.addEventListener('input', function() {
        const query = this.value.trim();

        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(() => {
            performSearch(query);
        }, 400);
    });

    // Enter key to search immediately
    input?.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            clearTimeout(debounceTimer);
            performSearch(this.value.trim());
        }
    });
});
