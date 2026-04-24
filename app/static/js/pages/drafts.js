/**
 * Drafts Page JavaScript
 */

let currentEditingId = null;
let currentViewingId = null;

/**
 * Generate URL-friendly slug from title
 */
function generateSlug(title) {
  if (!title) return '';
  return title.toLowerCase()
    .replace(/[^\w\s-]/g, '')      // Remove non-word chars
    .replace(/[\s_]+/g, '-')        // Replace spaces/underscores with hyphens
    .replace(/-+/g, '-')            // Remove multiple hyphens
    .trim()
    .replace(/^-|-$/g, '')          // Remove leading/trailing hyphens
    .substring(0, 100);             // Max 100 chars
}

// Check if there are remaining drafts and show empty state if needed
function checkEmptyState() {
  const container = document.querySelector('.drafts-container');
  const remainingRows = container.querySelectorAll('.draft-row');

  if (remainingRows.length === 0) {
    // Remove the header too
    const header = container.querySelector('.drafts-header');
    if (header) header.remove();

    // Add empty state
    container.innerHTML = `
      <div class="text-center py-5">
        <div class="mb-3 text-muted opacity-50"><i class="bi bi-file-earmark-text fs-1"></i></div>
        <p class="text-secondary fw-bold">No drafts found.</p>
        <a href="/create" class="btn btn-sm btn-outline-primary mt-2 rounded-pill px-4">Create New</a>
      </div>
    `;
  }
}

const initEditor = (initialContent) => {
  if (tinymce.get('editor-canvas')) {
    tinymce.remove('#editor-canvas');
  }

  tinymce.init({
    selector: '#editor-canvas',
    plugins: 'anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount',
    toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table | align lineheight | numlist bullist indent outdent | emoticons charmap | removeformat',
    height: 500,
    menubar: false,
    statusbar: false,
    setup: function (editor) {
      editor.on('init', function () {
        editor.setContent(initialContent || '');
      });
    }
  });
};

async function openViewModal(id) {
  currentViewingId = id;
  try {
    const res = await fetch(`/api/get_blog/${id}`);
    const data = await res.json();

    if (data.success) {
      const blog = data.blog;

      // Set title
      document.getElementById('view-modal-title').innerText = (blog.title || 'Untitled').replace(/\*\*/g, '');

      // Set status badge
      const statusBadge = document.getElementById('view-modal-status');
      const status = blog.status || 'DRAFT';
      statusBadge.innerText = status;
      statusBadge.className = 'status-badge status-' + status.toLowerCase().replace('_', '-');

      // Set category
      document.getElementById('view-modal-category').innerText = blog.category || 'General';

      // Set date
      if (blog.updated_at) {
        document.getElementById('view-modal-date').innerText = new Date(blog.updated_at).toLocaleDateString('en-US', {
          year: 'numeric', month: 'short', day: 'numeric'
        });
      }

      // Get content - use html field for formatted content
      let contentHtml = '';
      const content = blog.content;
      if (typeof content === 'object') {
        contentHtml = content.html || content.body || '';
      } else {
        contentHtml = content || '';
      }

      // Set content with proper HTML rendering
      document.getElementById('view-modal-content').innerHTML = contentHtml || '<p class="text-muted">No content available</p>';

      // Display TOC if available
      const tocContainer = document.getElementById('view-modal-toc');
      const tocContent = document.getElementById('view-modal-toc-content');
      if (typeof content === 'object' && content.toc && content.toc.length > 0) {
        let tocHtml = '<ul>';
        content.toc.forEach(item => {
          tocHtml += `<li class="toc-level-${item.level}">
            <a href="#${item.slug}">${item.text}</a>
          </li>`;
        });
        tocHtml += '</ul>';
        tocContent.innerHTML = tocHtml;
        tocContainer.classList.remove('d-none');
      } else if (typeof content === 'object' && content.toc_html) {
        tocContent.innerHTML = content.toc_html;
        tocContainer.classList.remove('d-none');
      } else {
        tocContainer.classList.add('d-none');
      }

      // Calculate reading time and word count from content
      const textContent = contentHtml.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
      const wordCount = textContent.split(' ').filter(w => w.length > 0).length;
      const readingTime = Math.ceil(wordCount / 200);

      document.getElementById('view-modal-reading-time').innerText = readingTime + ' min read';
      document.getElementById('view-modal-word-count').innerText = wordCount + ' words';

      // Set button actions
      document.getElementById('view-edit-btn').onclick = function() {
        bootstrap.Modal.getInstance(document.getElementById('viewModal')).hide();
        openEditModal(id);
      };

      document.getElementById('view-submit-btn').onclick = function() {
        bootstrap.Modal.getInstance(document.getElementById('viewModal')).hide();
        submitForReview(id);
      };

      // Show modal
      const viewModal = new bootstrap.Modal(document.getElementById('viewModal'));
      viewModal.show();
    } else {
      showToast({
        type: 'error',
        title: 'Error',
        message: data.message || 'Failed to load draft.',
        duration: 5000
      });
    }
  } catch (err) {
    console.error(err);
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Could not connect to server.',
      duration: 5000
    });
  }
}

async function openEditModal(id) {
  currentEditingId = id;
  try {
    const res = await fetch(`/api/get_blog/${id}`);
    const data = await res.json();
    if (data.success) {
      document.getElementById('modal-title').value = data.blog.title;

      // Set slug field
      document.getElementById('modal-slug').value = data.blog.slug || '';

      // Set SEO fields
      document.getElementById('modal-seo-title').value = data.blog.seo_title || '';
      document.getElementById('modal-seo-description').value = data.blog.seo_description || '';
      updateSeoCounters();

      const modalElement = document.getElementById('editModal');
      const editModal = new bootstrap.Modal(modalElement);
      editModal.show();

      // Get content - use html for editing (TinyMCE handles HTML)
      let content = '';
      const blogContent = data.blog.content;
      if (typeof blogContent === 'object') {
        content = blogContent.html || blogContent.body || '';
      } else {
        content = blogContent || '';
      }
      initEditor(content);

      // Setup slug event listeners
      const titleInput = document.getElementById('modal-title');
      const slugInput = document.getElementById('modal-slug');
      const regenerateBtn = document.getElementById('regenerate-slug');

      // Remove old event listeners by cloning
      const newTitleInput = titleInput.cloneNode(true);
      titleInput.parentNode.replaceChild(newTitleInput, titleInput);

      const newRegenerateBtn = regenerateBtn.cloneNode(true);
      regenerateBtn.parentNode.replaceChild(newRegenerateBtn, regenerateBtn);

      // Auto-generate slug from title on blur (only if slug is empty)
      newTitleInput.addEventListener('blur', function() {
        const slugField = document.getElementById('modal-slug');
        if (!slugField.value) {
          slugField.value = generateSlug(this.value);
        }
      });

      // Regenerate slug button
      newRegenerateBtn.addEventListener('click', function() {
        const title = document.getElementById('modal-title').value;
        document.getElementById('modal-slug').value = generateSlug(title);
      });

      // Setup SEO toggle
      setupSeoToggle();

    } else {
      showToast({
        type: 'error',
        title: 'Error',
        message: data.message || 'Failed to load draft.',
        duration: 5000
      });
    }
  } catch (err) {
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Could not connect to server.',
      duration: 5000
    });
  }
}

/**
 * Setup SEO section toggle and character counters
 */
function setupSeoToggle() {
  const toggleBtn = document.getElementById('seo-toggle-btn');
  const seoFields = document.getElementById('seo-fields');
  const seoTitle = document.getElementById('modal-seo-title');
  const seoDesc = document.getElementById('modal-seo-description');

  // Remove old listener by cloning
  const newToggleBtn = toggleBtn.cloneNode(true);
  toggleBtn.parentNode.replaceChild(newToggleBtn, toggleBtn);

  newToggleBtn.addEventListener('click', function() {
    const isVisible = seoFields.style.display !== 'none';
    seoFields.style.display = isVisible ? 'none' : 'block';
    this.classList.toggle('active', !isVisible);
  });

  // Character counters
  seoTitle.addEventListener('input', updateSeoCounters);
  seoDesc.addEventListener('input', updateSeoCounters);
}

/**
 * Update SEO character counters
 */
function updateSeoCounters() {
  const seoTitle = document.getElementById('modal-seo-title');
  const seoDesc = document.getElementById('modal-seo-description');
  document.getElementById('seo-title-count').textContent = seoTitle.value.length;
  document.getElementById('seo-desc-count').textContent = seoDesc.value.length;
}

async function saveModalChanges() {
  const updatedTitle = document.getElementById('modal-title').value;
  const editor = tinymce.get('editor-canvas');
  if (!editor) return;
  const updatedContent = editor.getContent();

  // Get slug (auto-generate if empty)
  let slug = document.getElementById('modal-slug').value.trim();
  if (!slug) {
    slug = generateSlug(updatedTitle);
  }

  // Get SEO fields
  const seoTitle = document.getElementById('modal-seo-title').value.trim();
  const seoDescription = document.getElementById('modal-seo-description').value.trim();

  const saveBtn = document.getElementById('save-changes-btn');
  const originalContent = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span> Saving...';

  try {
    const res = await fetch(`/api/update_blog/${currentEditingId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: updatedTitle,
        content: updatedContent,
        slug: slug,
        seo_title: seoTitle,
        seo_description: seoDescription
      })
    });

    const data = await res.json();
    if (data.success) {
      const row = document.querySelector(`#row-${currentEditingId} .title`);
      if (row) row.innerText = updatedTitle;
      bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
      saveBtn.disabled = false;
      saveBtn.innerHTML = originalContent;
      showToast({
        type: 'success',
        title: 'Changes Saved',
        message: 'Your draft has been updated successfully.',
        duration: 4000
      });
    } else {
      saveBtn.disabled = false;
      saveBtn.innerHTML = originalContent;
      showToast({
        type: 'error',
        title: 'Save Failed',
        message: data.error || 'Could not save changes.',
        duration: 5000
      });
    }
  } catch (err) {
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalContent;
    showToast({
      type: 'error',
      title: 'Error',
      message: 'Failed to save changes.',
      duration: 5000
    });
  }
}

async function submitForReview(id) {
  // Find and disable the dropdown button for this row
  const row = document.getElementById(`row-${id}`);
  const dropdownBtn = row ? row.querySelector('.btn-dropdown-trigger') : null;
  if (dropdownBtn) {
    dropdownBtn.disabled = true;
    dropdownBtn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
  }

  try {
    const res = await fetch(`/api/update_status/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: "UNDER_REVIEW" })
    });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'success',
        title: 'Submitted for Review',
        message: 'Your draft has been sent for approval.',
        duration: 4000
      });
      if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(20px)';
        setTimeout(() => {
          row.remove();
          checkEmptyState();
        }, 300);
      }
    } else {
      if (dropdownBtn) {
        dropdownBtn.disabled = false;
        dropdownBtn.innerHTML = '<i class="bi bi-three-dots-vertical"></i>';
      }
      showToast({
        type: 'error',
        title: 'Submission Failed',
        message: data.error || 'Could not submit for review.',
        duration: 5000
      });
    }
  } catch (e) {
    if (dropdownBtn) {
      dropdownBtn.disabled = false;
      dropdownBtn.innerHTML = '<i class="bi bi-three-dots-vertical"></i>';
    }
    showToast({
      type: 'error',
      title: 'Error',
      message: 'Failed to submit draft.',
      duration: 5000
    });
  }
}

async function deleteDraft(id) {
  // Find and disable the dropdown button for this row
  const row = document.getElementById(`row-${id}`);
  const dropdownBtn = row ? row.querySelector('.btn-dropdown-trigger') : null;
  if (dropdownBtn) {
    dropdownBtn.disabled = true;
    dropdownBtn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
  }

  try {
    const res = await fetch(`/api/delete_blog/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'warning',
        title: 'Draft Deleted',
        message: 'The draft has been permanently removed.',
        duration: 4000
      });
      if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(20px)';
        setTimeout(() => {
          row.remove();
          checkEmptyState();
        }, 300);
      }
    } else {
      if (dropdownBtn) {
        dropdownBtn.disabled = false;
        dropdownBtn.innerHTML = '<i class="bi bi-three-dots-vertical"></i>';
      }
      showToast({
        type: 'error',
        title: 'Delete Failed',
        message: data.error || 'Could not delete draft.',
        duration: 5000
      });
    }
  } catch (e) {
    if (dropdownBtn) {
      dropdownBtn.disabled = false;
      dropdownBtn.innerHTML = '<i class="bi bi-three-dots-vertical"></i>';
    }
    showToast({
      type: 'error',
      title: 'Error',
      message: 'Failed to delete draft.',
      duration: 5000
    });
  }
}
