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

async function analyzeDraft() {
    const draftId = document.getElementById('draft-select').value;
    const region = document.getElementById('draft-region').value;

    if (!draftId) {
        alert('Please select a draft to analyze');
        return;
    }

    currentDraftId = draftId;
    showLoading();

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
    document.getElementById('apply-seo-btn').style.display = 'none';

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
    if (!currentDraftId) {
        alert('No draft selected');
        return;
    }

    if (!confirm('This will update your draft with SEO-optimized content. Continue?')) {
        return;
    }

    const region = document.getElementById('draft-region').value;
    showLoading();

    try {
        const response = await fetch(`/api/seo/optimize-blog/${currentDraftId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ region })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
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
    document.getElementById('apply-seo-btn').style.display = 'none';
    document.getElementById('draft-select').value = '';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

async function runSEOAnalysis() {
    const title = document.getElementById('seo-title').value;
    const content = document.getElementById('seo-content').value;
    const region = document.getElementById('seo-region').value;

    if (!content) {
        alert('Please enter some content to analyze');
        return;
    }

    currentDraftId = null;
    document.getElementById('apply-seo-btn').style.display = 'none';
    document.getElementById('original-analysis-section').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'none';
    showLoading();

    try {
        const response = await fetch('/api/seo/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, region })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            displayResults(data.seo_analysis);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Network error. Please try again.');
        console.error(error);
    }
}

async function researchKeywords() {
    const topic = document.getElementById('seo-title').value;
    const region = document.getElementById('seo-region').value;

    if (!topic) {
        alert('Please enter a topic');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/seo/keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, region })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
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

function displayResults(analysis) {
    document.getElementById('results-section').style.display = 'block';

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
        diffBadge.textContent = primary.competition || 'UNKNOWN';
        diffBadge.className = 'badge bg-' + (primary.competition === 'LOW' ? 'success' : primary.competition === 'MEDIUM' ? 'warning' : 'danger');
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
    document.getElementById('results-section').style.display = 'block';

    // Hide score sections for keywords-only
    document.getElementById('seo-score-value').textContent = '--';
    document.getElementById('seo-score-label').textContent = 'Run full analysis for score';

    // Display seed keywords first
    const related = data.related_keywords || [];

    displayKeywords([...related]);

    // Primary from related
    if (related.length > 0) {
        const primary = related[0];
        document.getElementById('primary-keyword').textContent = primary.keyword;
        const diffBadge = document.getElementById('primary-difficulty');
        diffBadge.textContent = primary.competition || 'LOW';
        diffBadge.className = 'badge bg-' + (primary.competition === 'LOW' ? 'success' : primary.competition === 'MEDIUM' ? 'warning' : 'danger');
    }
}

function displayKeywords(keywords) {
    const container = document.getElementById('keywords-container');
    container.innerHTML = '';

    keywords.forEach(kw => {
        const difficulty = kw.difficulty_score || 50;
        const level = difficulty <= 30 ? 'easy' : difficulty <= 60 ? 'medium' : 'hard';

        const tag = document.createElement('span');
        tag.className = 'keyword-tag ' + level;
        tag.innerHTML = `
            ${kw.keyword}
            <span class="difficulty-badge bg-${level === 'easy' ? 'success' : level === 'medium' ? 'warning' : 'danger'} text-white">
                ${difficulty}
            </span>
        `;
        tag.onclick = () => {
            navigator.clipboard.writeText(kw.keyword);
            tag.style.transform = 'scale(0.95)';
            setTimeout(() => tag.style.transform = '', 150);
        };
        container.appendChild(tag);
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
    alert('Copied!');
}
