/**
 * Approval Queue Page JavaScript
 */

let currentBlogId = null;

async function openViewModal(id) {
  currentBlogId = id;
  try {
    const res = await fetch(`/api/get_blog/${id}`);
    const data = await res.json();

    if (data.success) {
      const blog = data.blog;
      const content = blog.content;

      // Set title
      document.getElementById('view-modal-title').innerText = (blog.title || 'Untitled').replace(/\*\*/g, '');

      // Set category
      document.getElementById('view-modal-category').innerText = blog.category || 'General';

      // Set author info
      const authorName = blog.author || blog.created_by || 'Unknown Author';
      document.getElementById('view-author-name').innerText = authorName;
      document.getElementById('view-author-avatar').innerText = authorName.substring(0, 2).toUpperCase();

      // Set date
      if (blog.updated_at) {
        document.getElementById('view-submit-date').innerText = 'Submitted on ' + new Date(blog.updated_at).toLocaleDateString('en-US', {
          year: 'numeric', month: 'short', day: 'numeric'
        });
      }

      // Get content - use html field for formatted content
      let contentHtml = '';
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

      // Calculate reading time and word count
      const textContent = contentHtml.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
      const wordCount = textContent.split(' ').filter(w => w.length > 0).length;
      const readingTime = Math.ceil(wordCount / 200);

      document.getElementById('view-modal-reading-time').innerText = readingTime + ' min read';
      document.getElementById('view-modal-word-count').innerText = wordCount + ' words';

      // Set button actions
      document.getElementById('view-approve-btn').onclick = function() {
        bootstrap.Modal.getInstance(document.getElementById('viewModal')).hide();
        approveBlog(id);
      };

      document.getElementById('view-reject-btn').onclick = function() {
        bootstrap.Modal.getInstance(document.getElementById('viewModal')).hide();
        rejectToDraft(id);
      };

      // Show modal
      const viewModal = new bootstrap.Modal(document.getElementById('viewModal'));
      viewModal.show();
    } else {
      showToast({
        type: 'error',
        title: 'Error',
        message: data.message || 'Failed to load blog.',
        duration: 5000
      });
    }
  } catch (err) {
    console.error(err);
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Failed to load blog content.',
      duration: 5000
    });
  }
}

async function openReviewModal(id) {
  currentBlogId = id;
  try {
    const res = await fetch(`/api/get_blog/${id}`);
    const data = await res.json();

    if (data.success) {
      const blog = data.blog;
      const content = blog.content;

      document.getElementById('viewTitle').innerText = (blog.title || 'Untitled').replace(/\*\*/g, '');

      // Set category
      document.getElementById('review-category').innerText = blog.category || 'General';

      // Get content - use html field for formatted content
      let contentHtml = '';
      if (typeof content === 'object') {
        contentHtml = content.html || content.body || '';
      } else {
        contentHtml = content || '';
      }

      document.getElementById('viewContent').innerHTML = contentHtml || '<p class="text-muted">No content</p>';

      // Display TOC if available
      const tocContainer = document.getElementById('review-modal-toc');
      const tocContent = document.getElementById('review-modal-toc-content');
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

      // Calculate reading time and word count
      const textContent = contentHtml.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
      const wordCount = textContent.split(' ').filter(w => w.length > 0).length;
      const readingTime = Math.ceil(wordCount / 200);

      document.getElementById('review-reading-time').innerText = readingTime + ' min read';
      document.getElementById('review-word-count').innerText = wordCount + ' words';

      const modalApproveBtn = document.getElementById('modalApproveBtn');
      modalApproveBtn.onclick = function () {
        const modalElem = document.getElementById('reviewModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElem);
        if (modalInstance) modalInstance.hide();
        approveBlog(id);
      };

      const modalRejectBtn = document.getElementById('modalRejectBtn');
      modalRejectBtn.onclick = function () {
        const modalElem = document.getElementById('reviewModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElem);
        if (modalInstance) modalInstance.hide();
        rejectToDraft(id);
      };

      const reviewModal = new bootstrap.Modal(document.getElementById('reviewModal'));
      reviewModal.show();
    } else {
      showToast({
        type: 'error',
        title: 'Error',
        message: data.message || 'Failed to load blog.',
        duration: 5000
      });
    }
  } catch (err) {
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Failed to load blog content.',
      duration: 5000
    });
  }
}

async function approveBlog(id) {
  try {
    const res = await fetch(`/api/update_status/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'PUBLISHED' })
    });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'success',
        title: 'Blog Published!',
        message: 'The blog has been approved and is now live on the site.',
        duration: 4000
      });
      const row = document.getElementById(`row-${id}`);
      if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(20px)';
        setTimeout(() => row.remove(), 300);
      }
    } else {
      showToast({
        type: 'error',
        title: 'Approval Failed',
        message: data.error || 'Could not approve the blog.',
        duration: 5000
      });
    }
  } catch (err) {
    showToast({
      type: 'error',
      title: 'Error',
      message: 'Failed to approve blog. Please try again.',
      duration: 5000
    });
  }
}

async function rejectToDraft(id) {
  try {
    const res = await fetch(`/api/update_status/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'DRAFT' })
    });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'warning',
        title: 'Moved to Drafts',
        message: 'The blog has been rejected and moved back to drafts.',
        duration: 4000
      });
      const row = document.getElementById(`row-${id}`);
      if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(20px)';
        setTimeout(() => row.remove(), 300);
      }
    } else {
      showToast({
        type: 'error',
        title: 'Rejection Failed',
        message: data.error || 'Could not reject the blog.',
        duration: 5000
      });
    }
  } catch (err) {
    showToast({
      type: 'error',
      title: 'Error',
      message: 'Failed to reject blog. Please try again.',
      duration: 5000
    });
  }
}
