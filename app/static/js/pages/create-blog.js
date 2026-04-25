/**
 * Create Blog Page JavaScript
 */

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
}

function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleGeneration();
  }
}

// Humanize toggle button
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('humanizeToggleBtn');
  const hiddenInput = document.getElementById('humanizeToggle');
  if (toggleBtn && hiddenInput) {
    toggleBtn.addEventListener('click', () => {
      const isActive = toggleBtn.classList.toggle('active');
      hiddenInput.value = isActive ? 'true' : 'false';
    });
  }
});

async function handleGeneration() {
  const promptInput = document.getElementById('prompt');
  const promptText = promptInput.value.trim();
  const loader = document.getElementById('loader');
  const genBtn = document.getElementById('genBtn');
  const promptBox = promptInput.closest('.prompt-box');

  if (!promptText) return;

  const enableHumanize = document.getElementById('humanizeToggle')?.value === 'true';

  loader.classList.remove('d-none');
  genBtn.disabled = true;
  promptInput.disabled = true;
  promptInput.blur();
  promptBox.classList.add('locked');

  // Update loader text based on humanize toggle
  const loaderText = loader.querySelector('span');
  if (loaderText) {
    loaderText.textContent = enableHumanize
      ? 'AI is generating and humanizing your content...'
      : 'AI is generating your content...';
  }

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: promptText, enable_humanize: enableHumanize })
    });

    const data = await response.json();

    if (data.success) {
      showToast({
        type: 'success',
        title: 'Blog Generated!',
        message: 'Your blog has been created and saved as a draft.',
        duration: 3000
      });
      setTimeout(() => {
        window.location.href = data.redirect || "/drafts";
      }, 1000);
    } else {
      showToast({
        type: 'error',
        title: 'Generation Failed',
        message: data.error || 'Please try again.',
        duration: 5000
      });
      genBtn.disabled = false;
      promptInput.disabled = false;
      promptBox.classList.remove('locked');
      loader.classList.add('d-none');
    }
  } catch (err) {
    console.error("Error:", err);
    showToast({
      type: 'error',
      title: 'Connection Error',
      message: 'Something went wrong. Check your connection.',
      duration: 5000
    });
    genBtn.disabled = false;
    promptInput.disabled = false;
    promptBox.classList.remove('locked');
    loader.classList.add('d-none');
  }
}
