/**
 * Categories Page JavaScript
 */

// Add Category
document.getElementById('addCategoryForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const name = formData.get('name').trim();

  try {
    const res = await fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'success',
        title: 'Category Created',
        message: `"${name}" has been added successfully.`,
        duration: 3000
      });
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast({
        type: 'error',
        title: 'Error',
        message: data.error || 'Failed to create category.',
        duration: 5000
      });
    }
  } catch (err) {
    console.error(err);
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Failed to add category.',
      duration: 5000
    });
  }
});

// Edit Category Modal Opener
function openEditModal(id, name) {
  document.getElementById('editCategoryId').value = id;
  document.getElementById('editCategoryName').value = name;
  const editModal = new bootstrap.Modal(document.getElementById('editCategoryModal'));
  editModal.show();
}

// Submit Edit
document.getElementById('editCategoryForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('editCategoryId').value;
  const name = document.getElementById('editCategoryName').value.trim();

  try {
    const res = await fetch(`/api/edit_category/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'success',
        title: 'Category Updated',
        message: `Category renamed to "${name}".`,
        duration: 3000
      });
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast({
        type: 'error',
        title: 'Update Failed',
        message: data.error || 'Could not update category.',
        duration: 5000
      });
    }
  } catch (err) {
    console.error(err);
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Failed to update category.',
      duration: 5000
    });
  }
});

// Delete Category
async function deleteCategory(id) {
  try {
    const res = await fetch(`/api/delete_category/${id}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (data.success) {
      showToast({
        type: 'warning',
        title: 'Category Deleted',
        message: 'The category has been removed.',
        duration: 3000
      });
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast({
        type: 'error',
        title: 'Delete Failed',
        message: data.error || 'Could not delete category.',
        duration: 5000
      });
    }
  } catch (err) {
    console.error(err);
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Failed to delete category.',
      duration: 5000
    });
  }
}

// Simple Search Filter
document.getElementById('searchInput').addEventListener('keyup', function () {
  const value = this.value.toLowerCase();
  document.querySelectorAll('.category-item').forEach(item => {
    const text = item.querySelector('.col-name').innerText.toLowerCase();
    item.style.setProperty('display', text.includes(value) ? 'flex' : 'none', 'important');
  });
});
