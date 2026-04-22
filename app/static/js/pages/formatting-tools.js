/**
 * Formatting Tools Page JavaScript
 */

let formattedData = null;
let draftsData = [];
let selectedDraftId = null;
let selectedDraftData = null;

// Load drafts on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDrafts();
});

async function loadDrafts() {
    try {
        const response = await fetch('/api/seo/drafts');
        const data = await response.json();

        if (data.success && data.drafts) {
            draftsData = data.drafts;
            const select = document.getElementById('draft-select');
            select.innerHTML = '<option value="">-- Select a draft to load --</option>';

            data.drafts.forEach(draft => {
                const option = document.createElement('option');
                option.value = draft.id;
                option.textContent = (draft.title || 'Untitled').replace(/\*\*/g, '').substring(0, 60);
                if (draft.title && draft.title.length > 60) option.textContent += '...';
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading drafts:', error);
    }
}

function refreshDrafts() {
    loadDrafts();
}

async function loadDraftContent() {
    const select = document.getElementById('draft-select');
    const draftId = select.value;

    if (!draftId) return;

    selectedDraftId = draftId;

    try {
        const response = await fetch(`/api/get_blog/${draftId}`);
        const data = await response.json();

        if (data.success && data.blog) {
            const blog = data.blog;
            selectedDraftData = blog;

            // Set title
            document.getElementById('format-title').value = (blog.title || '').replace(/\*\*/g, '');

            // Get content - prefer markdown if available
            let content = '';
            if (typeof blog.content === 'object') {
                content = blog.content.markdown || blog.content.original_markdown || blog.content.body || '';
            } else {
                content = blog.content || '';
            }

            // If content looks like HTML, try to use markdown version
            if (content.startsWith('<') && blog.content && blog.content.markdown) {
                content = blog.content.markdown;
            }

            document.getElementById('format-content').value = content;
        }
    } catch (error) {
        console.error('Error loading draft:', error);
        alert('Failed to load draft content');
    }
}

async function viewSelectedDraft() {
    const select = document.getElementById('draft-select');
    const draftId = select.value;

    if (!draftId) {
        alert('Please select a draft first');
        return;
    }

    try {
        const response = await fetch(`/api/get_blog/${draftId}`);
        const data = await response.json();

        if (data.success && data.blog) {
            const blog = data.blog;
            selectedDraftData = blog;
            selectedDraftId = draftId;

            // Set title
            document.getElementById('view-draft-title').innerText = (blog.title || 'Untitled').replace(/\*\*/g, '');

            // Set category
            document.getElementById('view-draft-category').innerText = blog.category || 'General';

            // Set date
            if (blog.updated_at) {
                document.getElementById('view-draft-date').innerText = new Date(blog.updated_at).toLocaleDateString('en-US', {
                    year: 'numeric', month: 'short', day: 'numeric'
                });
            }

            // Get content
            let contentHtml = '';
            if (typeof blog.content === 'object') {
                contentHtml = blog.content.html || blog.content.body || '';
            } else {
                contentHtml = blog.content || '';
            }

            document.getElementById('view-draft-content').innerHTML = contentHtml || '<p class="text-muted">No content</p>';

            // Calculate stats
            const textContent = contentHtml.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
            const wordCount = textContent.split(' ').filter(w => w.length > 0).length;
            const readingTime = Math.ceil(wordCount / 200);

            document.getElementById('view-draft-reading-time').innerText = readingTime + ' min read';
            document.getElementById('view-draft-word-count').innerText = wordCount + ' words';

            // Show modal
            const viewModal = new bootstrap.Modal(document.getElementById('viewDraftModal'));
            viewModal.show();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to load draft');
    }
}

function useThisDraft() {
    if (selectedDraftData) {
        // Set title
        document.getElementById('format-title').value = (selectedDraftData.title || '').replace(/\*\*/g, '');

        // Get content - prefer markdown
        let content = '';
        if (typeof selectedDraftData.content === 'object') {
            content = selectedDraftData.content.markdown || selectedDraftData.content.original_markdown || selectedDraftData.content.body || '';
        } else {
            content = selectedDraftData.content || '';
        }

        document.getElementById('format-content').value = content;

        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('viewDraftModal')).hide();

        // Update select to show selected draft
        document.getElementById('draft-select').value = selectedDraftId;
    }
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

async function formatContent() {
    const title = document.getElementById('format-title').value;
    const content = document.getElementById('format-content').value;

    if (!content.trim()) {
        alert('Please enter some content to format');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/format', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            formattedData = data.formatted;
            displayResults(data.formatted);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Network error. Please try again.');
        console.error(error);
    }
}

function displayResults(data) {
    document.getElementById('results-section').style.display = 'block';

    // Reading time
    document.getElementById('reading-time').innerHTML =
        `<i class="bi bi-clock"></i> ${data.reading_time}`;

    // Statistics
    const stats = data.statistics || {};
    document.getElementById('stat-words').textContent = stats.word_count || 0;
    document.getElementById('stat-sentences').textContent = stats.sentence_count || 0;
    document.getElementById('stat-paragraphs').textContent = stats.paragraph_count || 0;
    document.getElementById('stat-characters').textContent = stats.character_count || 0;

    // Feature badges - we need to check the content for these
    const content = document.getElementById('format-content').value;
    updateFeatureBadge('has-code', /```[\s\S]*?```|`[^`]+`/.test(content));
    updateFeatureBadge('has-images', /!\[.*?\]\(.*?\)/.test(content));
    updateFeatureBadge('has-tables', /\|.*\|.*\|/.test(content));

    // Table of Contents
    const tocPreview = document.getElementById('toc-preview');
    if (data.toc && data.toc.length > 0) {
        let tocHtml = '<ul>';
        data.toc.forEach(item => {
            tocHtml += `<li class="toc-level-${item.level}">
                <a href="#${item.slug}">${item.text}</a>
            </li>`;
        });
        tocHtml += '</ul>';
        tocPreview.innerHTML = tocHtml;
    } else {
        tocPreview.innerHTML = '<p class="text-muted">No headings found</p>';
    }

    // HTML Preview
    document.getElementById('html-preview').innerHTML = data.html;

    // Raw HTML
    document.getElementById('raw-html').value = data.html;

    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function updateFeatureBadge(id, hasFeature) {
    const badge = document.getElementById(id);
    badge.className = 'feature-badge ' + (hasFeature ? 'has' : 'no');
}

function clearAll() {
    document.getElementById('format-title').value = '';
    document.getElementById('format-content').value = '';
    document.getElementById('results-section').style.display = 'none';
    formattedData = null;
}

function copyTOC() {
    if (!formattedData || !formattedData.toc) {
        alert('No TOC available');
        return;
    }

    let tocMarkdown = '## Table of Contents\n\n';
    formattedData.toc.forEach(item => {
        const indent = '  '.repeat(item.level - 1);
        tocMarkdown += `${indent}- [${item.text}](#${item.slug})\n`;
    });

    navigator.clipboard.writeText(tocMarkdown);
    alert('TOC copied to clipboard!');
}

function copyHTML() {
    const html = document.getElementById('html-preview').innerHTML;
    navigator.clipboard.writeText(html);
    alert('HTML copied to clipboard!');
}

function copyRawHTML() {
    const rawHtml = document.getElementById('raw-html').value;
    navigator.clipboard.writeText(rawHtml);
    alert('Raw HTML copied to clipboard!');
}
