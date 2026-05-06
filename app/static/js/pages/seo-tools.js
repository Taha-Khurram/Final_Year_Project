/**
 * SEO Tools Page JavaScript
 */

let currentDraftId = null;
let currentDraftTitle = null;
let originalAnalysisData = null;

// Load drafts on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDrafts();
});

async function loadDrafts() {
    const select = document.getElementById('draft-select');
    select.innerHTML = '<option value="">-- Loading... --</option>';

    try {
        const response = await fetch('/api/seo/drafts');
        const data = await response.json();

        if (data.success && data.drafts.length > 0) {
            select.innerHTML = '<option value="">-- Select a draft --</option>';
            data.drafts.forEach(draft => {
                const option = document.createElement('option');
                option.value = draft.id;
                option.textContent = `${draft.title} (${draft.updated_at || 'No date'})`;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">-- No drafts found --</option>';
        }
    } catch (error) {
        console.error('Error loading drafts:', error);
        select.innerHTML = '<option value="">-- Error loading drafts --</option>';
    }
}

async function researchKeywordsForDraft() {
    const draftId = document.getElementById('draft-select').value;
    const region = document.getElementById('draft-region').value;

    if (!draftId) {
        alert('Please select a draft first');
        return;
    }

    showLoading('Researching keywords for your draft...');

    try {
        // First get the draft content
        const draftRes = await fetch(`/api/get_blog/${draftId}`);
        const draftData = await draftRes.json();

        if (!draftData.success) {
            hideLoading();
            alert('Error loading draft');
            return;
        }

        const topic = draftData.blog.title || '';

        // Research keywords using the draft title as topic
        const response = await fetch('/api/seo/keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, region })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            currentDraftId = draftId;
            currentDraftTitle = topic;
            displayKeywordsOnly(data);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Network error. Please try again.');
        console.error(error);
    }
}

async function analyzeDraft() {
    const draftId = document.getElementById('draft-select').value;
    const region = document.getElementById('draft-region').value;

    if (!draftId) {
        alert('Please select a draft to analyze');
        return;
    }

    currentDraftId = draftId;
    showLoading('Analyzing SEO performance...');

    try {
        const response = await fetch(`/api/seo/analyze-draft/${draftId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ region })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            currentDraftTitle = data.blog_title;
            originalAnalysisData = data.original_analysis;
            displayOriginalAnalysis(data.original_analysis, data.blog_title);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Network error. Please try again.');
        console.error(error);
    }
}

function displayOriginalAnalysis(analysis, title) {
    // Hide other sections, show original analysis
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'none';
    document.getElementById('original-analysis-section').style.display = 'block';

    // Score
    const score = analysis.seo_score?.total || 0;
    const grade = analysis.seo_score?.grade || 'N/A';
    const scoreCircle = document.getElementById('original-score-circle');
    scoreCircle.className = 'score-circle ' + (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
    document.getElementById('original-score-value').textContent = score;
    document.getElementById('original-score-grade').textContent = `Grade: ${grade}`;

    // Issues
    const issuesList = document.getElementById('original-issues-list');
    issuesList.innerHTML = '';
    const issues = analysis.issues || [];
    if (issues.length === 0) {
        issuesList.innerHTML = '<li class="text-success"><i class="bi bi-check-circle me-2"></i>No major issues found!</li>';
    } else {
        issues.forEach(issue => {
            const icon = issue.severity === 'high' ? 'exclamation-triangle text-danger' :
                        issue.severity === 'medium' ? 'exclamation-circle text-warning' : 'info-circle text-info';
            issuesList.innerHTML += `<li class="mb-2"><i class="bi bi-${icon} me-2"></i>${issue.message}</li>`;
        });
    }

    // Recommendations
    const recsContainer = document.getElementById('original-recommendations');
    recsContainer.innerHTML = '';
    const recs = analysis.recommendations || [];
    recs.forEach(rec => {
        recsContainer.innerHTML += `<div class="recommendation-item">${rec}</div>`;
    });

    // Stats
    document.getElementById('original-word-count').textContent = analysis.word_count || 0;
    document.getElementById('original-readability').textContent = analysis.readability?.flesch_score?.toFixed(0) || '--';
    document.getElementById('original-headings').textContent = analysis.headings?.total || 0;
    document.getElementById('original-links').textContent = analysis.links?.total || 0;

    // Scroll to section
    document.getElementById('original-analysis-section').scrollIntoView({ behavior: 'smooth' });
}

async function applyOptimizationToDraft() {
    // Get draft ID from current state or from select dropdown
    const draftId = currentDraftId || document.getElementById('draft-select').value;

    if (!draftId) {
        alert('Please select a draft first');
        return;
    }

    // Show custom confirmation modal
    const confirmed = await showConfirmModal();
    if (!confirmed) {
        return;
    }

    currentDraftId = draftId;
    const region = document.getElementById('draft-region').value;
    showLoading('Applying SEO optimization to your draft...');

    try {
        const response = await fetch(`/api/seo/optimize-blog/${draftId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ region })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            currentDraftTitle = data.new_title || currentDraftTitle;
            displayComparison(data, currentDraftTitle);
            loadDrafts(); // Refresh drafts list
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Network error. Please try again.');
        console.error(error);
    }
}

function displayComparison(data, originalTitle) {
    // Hide other sections, show comparison
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('original-analysis-section').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'block';

    // Scores
    const scoreBefore = data.original_score || 0;
    const scoreAfter = data.seo_score || 0;
    const improvement = data.score_improvement || 0;

    document.getElementById('compare-score-before').textContent = scoreBefore;
    document.getElementById('compare-score-after').textContent = scoreAfter;

    const badge = document.getElementById('improvement-badge');
    badge.textContent = (improvement >= 0 ? '+' : '') + improvement + ' points';
    badge.className = 'improvement-badge ' + (improvement >= 0 ? 'positive' : 'negative');

    // Detailed comparison
    const comparison = data.comparison?.breakdown_comparison || {};
    document.getElementById('cmp-content-before').textContent = comparison.content_length?.before || '--';
    document.getElementById('cmp-content-after').textContent = comparison.content_length?.after || '--';
    document.getElementById('cmp-headings-before').textContent = comparison.headings?.before || '--';
    document.getElementById('cmp-headings-after').textContent = comparison.headings?.after || '--';
    document.getElementById('cmp-keywords-before').textContent = comparison.keywords?.before || '--';
    document.getElementById('cmp-keywords-after').textContent = comparison.keywords?.after || '--';
    document.getElementById('cmp-readability-before').textContent = comparison.readability?.before || '--';
    document.getElementById('cmp-readability-after').textContent = comparison.readability?.after || '--';
    document.getElementById('cmp-title-before').textContent = comparison.title?.before || '--';
    document.getElementById('cmp-title-after').textContent = comparison.title?.after || '--';

    // Title comparison
    document.getElementById('compare-title-before').value = originalTitle || '';
    document.getElementById('compare-title-after').value = data.new_title || '';

    // Changes made
    const changesList = document.getElementById('changes-list');
    changesList.innerHTML = '';
    const changes = data.changes_made || [];
    if (changes.length === 0) {
        changesList.innerHTML = '<li><i class="bi bi-info-circle"></i><span>Content optimized with target keywords</span></li>';
    } else {
        changes.forEach(change => {
            let html = `<li><i class="bi bi-check2"></i><div>`;
            html += `<strong>${change.description}</strong>`;
            if (change.before && change.after) {
                html += `<br><small class="text-muted">Before: ${change.before}</small>`;
                html += `<br><small class="text-success">After: ${change.after}</small>`;
            }
            html += `</div></li>`;
            changesList.innerHTML += html;
        });
    }

    // Scroll to section
    document.getElementById('comparison-section').scrollIntoView({ behavior: 'smooth' });
}

function resetAnalysis() {
    currentDraftId = null;
    currentDraftTitle = null;
    originalAnalysisData = null;

    document.getElementById('results-section').style.display = 'none';
    document.getElementById('original-analysis-section').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'none';
    document.getElementById('draft-select').value = '';

    // Reset visibility of subsections for next use
    document.getElementById('seo-score-section').style.display = '';
    document.getElementById('seo-checklist-section').style.display = '';
    document.getElementById('optimized-title-section').style.display = '';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoading(message = 'AI is analyzing your content...') {
    document.getElementById('seo-loader-text').textContent = message;
    document.getElementById('seo-loader').classList.remove('d-none');
}

function hideLoading() {
    document.getElementById('seo-loader').classList.add('d-none');
}

function displayResults(analysis) {
    // Hide other sections
    document.getElementById('original-analysis-section').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'none';

    // Show results section and all its subsections
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('seo-score-section').style.display = '';
    document.getElementById('seo-checklist-section').style.display = '';
    document.getElementById('optimized-title-section').style.display = '';

    // SEO Score - handle both old and new format
    let score = 0;
    let grade = 'N/A';

    // Try new format first (from optimize_blog)
    if (analysis.optimized?.seo_score) {
        score = analysis.optimized.seo_score;
        grade = analysis.optimized.seo_grade || 'N/A';
    }
    // Try direct seo_score (from analyze_content)
    else if (analysis.seo_score?.total) {
        score = analysis.seo_score.total;
        grade = analysis.seo_score.grade || 'N/A';
    }
    // Fallback to original analysis
    else if (analysis.original_analysis?.seo_score?.total) {
        score = analysis.original_analysis.seo_score.total;
        grade = analysis.original_analysis.seo_score.grade || 'N/A';
    }

    const scoreCircle = document.getElementById('seo-score-circle');
    const scoreValue = document.getElementById('seo-score-value');
    const scoreLabel = document.getElementById('seo-score-label');

    scoreValue.textContent = score;
    scoreCircle.className = 'score-circle ' + (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
    scoreLabel.textContent = score >= 70 ? `Excellent! (${grade})` : score >= 40 ? `Good (${grade})` : `Needs work (${grade})`;

    // Primary Keyword
    const primary = analysis.keyword_research?.primary_keyword;
    if (primary) {
        document.getElementById('primary-keyword').textContent = primary.keyword || '--';
        const diffBadge = document.getElementById('primary-difficulty');
        const comp = (primary.competition || 'UNKNOWN').toUpperCase();
        diffBadge.textContent = comp;
        diffBadge.className = 'badge bg-' + (comp === 'LOW' ? 'success' : comp === 'MEDIUM' ? 'warning' : 'danger');

        // Show detailed info
        const infoEl = document.getElementById('primary-keyword-info');
        const volume = primary.search_volume ? primary.search_volume.toLocaleString() : 'N/A';
        const cpc = primary.cpc ? `$${parseFloat(primary.cpc).toFixed(2)}` : 'N/A';
        const difficulty = primary.difficulty_score || '--';
        infoEl.innerHTML = `
            <span class="badge bg-light text-dark me-2"><i class="bi bi-bar-chart me-1"></i>Volume: ${volume}</span>
            <span class="badge bg-light text-dark me-2"><i class="bi bi-currency-dollar me-1"></i>CPC: ${cpc}</span>
            <span class="badge bg-light text-dark me-2"><i class="bi bi-speedometer2 me-1"></i>Difficulty: ${difficulty}/100</span>
        `;
    }

    // Keywords - use all_opportunities if available
    const keywords = analysis.keyword_research?.all_opportunities || analysis.keyword_research?.all_keywords || [];
    displayKeywords(keywords);

    // Optimized Title
    document.getElementById('optimized-title').value = analysis.optimized?.optimized_title || '';

    // SEO Checklist - use new keyword_placement format
    const placement = analysis.optimized?.keyword_placement || {};
    const seoAnalysis = analysis.optimized?.seo_analysis || analysis.original_analysis || {};
    const links = seoAnalysis.links || {};

    displayChecklist({
        keyword_in_title: placement.in_title || false,
        keyword_in_first_100: placement.in_first_paragraph || false,
        keyword_density: placement.density >= 1.0 && placement.density <= 2.5,
        meta_description: !!analysis.optimized?.meta_description,
        headings_have_keywords: placement.in_headings || false,
        internal_links: links.internal_count > 0
    });

    // Score Breakdown - populate progress bars
    const scoreBreakdown = seoAnalysis.seo_score?.breakdown || analysis.original_analysis?.seo_score?.breakdown || {};
    updateScoreBreakdown(scoreBreakdown);

    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function updateScoreBreakdown(breakdown) {
    const categories = {
        'content': 'content_length',
        'headings': 'headings',
        'keywords': 'keywords',
        'readability': 'readability',
        'links': 'links',
        'title': 'title'
    };

    for (const [elemId, dataKey] of Object.entries(categories)) {
        const data = breakdown[dataKey];
        if (data) {
            const bar = document.getElementById(`score-${elemId}`);
            const val = document.getElementById(`score-${elemId}-val`);
            if (bar) bar.style.width = `${data.score}%`;
            if (val) val.textContent = `${data.score}/100`;
        }
    }
}

function displayKeywordsOnly(data) {
    // Hide other sections first
    document.getElementById('original-analysis-section').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'none';

    // Show results section
    document.getElementById('results-section').style.display = 'block';

    // Hide SEO-specific sections (not relevant for keyword research only)
    document.getElementById('seo-score-section').style.display = 'none';
    document.getElementById('seo-checklist-section').style.display = 'none';
    document.getElementById('optimized-title-section').style.display = 'none';

    // Display keywords
    const related = data.related_keywords || [];
    displayKeywords([...related]);

    // Primary from related with full data
    if (related.length > 0) {
        const primary = related[0];
        document.getElementById('primary-keyword').textContent = primary.keyword;
        const diffBadge = document.getElementById('primary-difficulty');
        const comp = (primary.competition || 'low').toUpperCase();
        diffBadge.textContent = comp;
        diffBadge.className = 'badge bg-' + (comp === 'LOW' ? 'success' : comp === 'MEDIUM' ? 'warning' : 'danger');

        // Show detailed info for primary keyword
        const infoEl = document.getElementById('primary-keyword-info');
        const volume = primary.search_volume ? primary.search_volume.toLocaleString() : 'N/A';
        const cpc = primary.cpc ? `$${parseFloat(primary.cpc).toFixed(2)}` : 'N/A';
        const difficulty = primary.difficulty_score || '--';
        infoEl.innerHTML = `
            <span class="badge bg-light text-dark me-2"><i class="bi bi-bar-chart me-1"></i>Volume: ${volume}</span>
            <span class="badge bg-light text-dark me-2"><i class="bi bi-currency-dollar me-1"></i>CPC: ${cpc}</span>
            <span class="badge bg-light text-dark me-2"><i class="bi bi-speedometer2 me-1"></i>Difficulty: ${difficulty}/100</span>
        `;
    }

    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function displayKeywords(keywords) {
    const container = document.getElementById('keywords-container');
    container.innerHTML = '';

    keywords.forEach(kw => {
        const difficulty = kw.difficulty_score || 50;
        const level = difficulty <= 30 ? 'easy' : difficulty <= 60 ? 'medium' : 'hard';
        const volume = kw.search_volume ? kw.search_volume.toLocaleString() : '--';
        const cpc = kw.cpc ? `$${parseFloat(kw.cpc).toFixed(2)}` : '--';
        const competition = (kw.competition || 'medium').toLowerCase();

        const card = document.createElement('div');
        card.className = 'keyword-card mb-2 p-3 border rounded d-flex justify-content-between align-items-center';
        card.style.cursor = 'pointer';
        card.style.transition = 'all 0.2s ease';
        card.innerHTML = `
            <div class="d-flex align-items-center gap-2">
                <span class="badge bg-${level === 'easy' ? 'success' : level === 'medium' ? 'warning' : 'danger'} text-white" style="min-width: 32px; text-align: center;">
                    ${difficulty}
                </span>
                <strong class="keyword-text">${kw.keyword}</strong>
            </div>
            <div class="d-flex align-items-center gap-3 text-muted small">
                <span title="Monthly Search Volume"><i class="bi bi-bar-chart"></i> ${volume}</span>
                <span title="Cost Per Click"><i class="bi bi-currency-dollar"></i> ${cpc}</span>
                <span title="Competition Level" class="badge bg-${competition === 'low' ? 'success' : competition === 'medium' ? 'warning' : 'danger'} bg-opacity-25 text-${competition === 'low' ? 'success' : competition === 'medium' ? 'warning' : 'danger'}">
                    ${competition}
                </span>
            </div>
        `;
        card.onclick = () => {
            navigator.clipboard.writeText(kw.keyword);
            card.style.transform = 'scale(0.98)';
            card.style.background = '#f0f9ff';
            setTimeout(() => { card.style.transform = ''; card.style.background = ''; }, 200);
            showCopyToast();
        };
        container.appendChild(card);
    });
}

function displayChecklist(checks) {
    const checklist = document.getElementById('seo-checklist');
    checklist.innerHTML = '';

    const items = [
        { key: 'keyword_in_title', label: 'Keyword in title' },
        { key: 'keyword_in_first_100', label: 'Keyword in first 100 words' },
        { key: 'keyword_density', label: 'Optimal keyword density (1-2%)' },
        { key: 'meta_description', label: 'Meta description present' },
        { key: 'headings_have_keywords', label: 'Keywords in headings' },
        { key: 'internal_links', label: 'Internal linking opportunities' }
    ];

    items.forEach(item => {
        const passed = checks[item.key] || false;
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="check-icon ${passed ? 'pass' : 'fail'}">
                <i class="bi bi-${passed ? 'check' : 'x'}"></i>
            </span>
            <span>${item.label}</span>
        `;
        checklist.appendChild(li);
    });
}

function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    el.select();
    document.execCommand('copy');
    showCopyToast();
}

// Show copy toast notification
function showCopyToast() {
    const toast = document.getElementById('copy-toast');
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

// Custom confirmation modal
function showConfirmModal() {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirm-modal');
        const okBtn = document.getElementById('confirm-ok-btn');
        const cancelBtn = document.getElementById('confirm-cancel-btn');

        // Show modal
        modal.classList.add('active');

        // Handle OK click
        const handleOk = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(true);
        };

        // Handle Cancel click
        const handleCancel = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(false);
        };

        // Handle clicking outside the modal
        const handleOutsideClick = (e) => {
            if (e.target === modal) {
                handleCancel();
            }
        };

        // Handle escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                handleCancel();
            }
        };

        // Cleanup event listeners
        const cleanup = () => {
            okBtn.removeEventListener('click', handleOk);
            cancelBtn.removeEventListener('click', handleCancel);
            modal.removeEventListener('click', handleOutsideClick);
            document.removeEventListener('keydown', handleEscape);
        };

        // Add event listeners
        okBtn.addEventListener('click', handleOk);
        cancelBtn.addEventListener('click', handleCancel);
        modal.addEventListener('click', handleOutsideClick);
        document.addEventListener('keydown', handleEscape);
    });
}

// =========================================
// URL SEO ANALYSIS
// =========================================
async function analyzeUrlSeo() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a URL to analyze');
        return;
    }

    showLoading('Analyzing URL SEO... This may take 10-20 seconds.');

    try {
        const response = await fetch('/api/seo/analyze-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            displayUrlResults(data);
        } else {
            alert('Error: ' + (data.error || 'Failed to analyze URL'));
        }
    } catch (error) {
        hideLoading();
        alert('Network error. Please try again.');
        console.error(error);
    }
}

function displayUrlResults(data) {
    const section = document.getElementById('url-results-section');
    section.style.display = 'block';

    // URL & Title
    const link = document.getElementById('url-result-link');
    link.href = data.url || '#';
    link.textContent = data.url || '--';
    document.getElementById('url-result-title').textContent = data.title || 'N/A';
    document.getElementById('url-result-description').textContent = data.description || 'N/A';

    // Score
    const score = data.score || 0;
    const scoreCircle = document.getElementById('url-score-circle');
    scoreCircle.className = 'score-circle ' + (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
    document.getElementById('url-score-value').textContent = score;

    // Content Analysis
    const content = data.content_analysis || {};
    document.getElementById('url-word-count').textContent = content.word_count || '--';
    document.getElementById('url-title-length').textContent = content.title_length || '--';
    document.getElementById('url-desc-length').textContent = content.description_length || '--';
    document.getElementById('url-load-time').textContent = data.load_time || '--';

    // Technical SEO Checks
    const technical = data.technical || {};
    const techContainer = document.getElementById('url-technical-checks');
    techContainer.innerHTML = '';
    const techChecks = [
        { key: 'ssl', label: 'SSL/HTTPS', icon: 'shield-lock' },
        { key: 'mobile_friendly', label: 'Mobile Friendly', icon: 'phone' },
        { key: 'robots_txt', label: 'Robots.txt', icon: 'robot' },
        { key: 'sitemap', label: 'Sitemap', icon: 'diagram-3' },
    ];
    techChecks.forEach(check => {
        const passed = technical[check.key];
        techContainer.innerHTML += `
            <div class="col-md-3 col-6">
                <div class="border rounded p-2 text-center ${passed ? 'border-success' : 'border-danger'}">
                    <i class="bi bi-${check.icon} ${passed ? 'text-success' : 'text-danger'}"></i>
                    <div class="small fw-bold">${check.label}</div>
                    <span class="badge bg-${passed ? 'success' : 'danger'}">${passed ? 'Pass' : 'Fail'}</span>
                </div>
            </div>
        `;
    });

    if (technical.canonical) {
        techContainer.innerHTML += `
            <div class="col-12 mt-2">
                <small class="text-muted"><strong>Canonical:</strong> ${technical.canonical}</small>
            </div>
        `;
    }
    if (technical.lang) {
        techContainer.innerHTML += `
            <div class="col-12">
                <small class="text-muted"><strong>Language:</strong> ${technical.lang}</small>
            </div>
        `;
    }

    // Issues & Warnings
    const issuesContainer = document.getElementById('url-issues-container');
    const issues = data.issues || [];
    const warnings = data.warnings || [];
    const allIssues = [...issues, ...warnings];

    if (allIssues.length > 0) {
        issuesContainer.innerHTML = allIssues.map(issue => {
            const text = typeof issue === 'string' ? issue : (issue.message || issue.description || JSON.stringify(issue));
            const isWarning = warnings.includes(issue);
            return `<div class="d-flex align-items-start gap-2 mb-2">
                <i class="bi bi-${isWarning ? 'exclamation-circle text-warning' : 'x-circle text-danger'} mt-1"></i>
                <span>${text}</span>
            </div>`;
        }).join('');
    } else {
        issuesContainer.innerHTML = '<p class="text-success mb-0"><i class="bi bi-check-circle me-2"></i>No issues found!</p>';
    }

    // Passed Checks
    const passedContainer = document.getElementById('url-passed-container');
    const passed = data.passed || [];
    if (passed.length > 0) {
        passedContainer.innerHTML = passed.map(item => {
            const text = typeof item === 'string' ? item : (item.message || item.description || JSON.stringify(item));
            return `<div class="d-flex align-items-start gap-2 mb-2">
                <i class="bi bi-check-circle text-success mt-1"></i>
                <span>${text}</span>
            </div>`;
        }).join('');
    } else {
        passedContainer.innerHTML = '<p class="text-muted mb-0">Detailed checks not available for this URL.</p>';
    }

    // Scroll to results
    section.scrollIntoView({ behavior: 'smooth' });
}
