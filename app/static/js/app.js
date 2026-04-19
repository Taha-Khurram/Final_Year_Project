/**
 * Scriptly AI - Main Application Logic
 */

async function handleGeneration() {
    const promptInput = document.getElementById('prompt');
    const genBtn = document.getElementById('genBtn');
    const loader = document.getElementById('loader');

    if (!promptInput.value.trim()) {
        alert("Please enter a blog topic or prompt.");
        return;
    }

    // UI: Show loading state
    genBtn.disabled = true;
    loader.classList.remove('d-none');
    promptInput.classList.add('opacity-50');

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: promptInput.value,
                user_id: 'admin_user_01' // In production, get from auth context
            })
        });

        const result = await response.json();

        if (result.success) {
            // UI: Success feedback
            console.log("Success! Blog ID:", result.blog_id);
            // Redirect to Approval Queue automatically
            window.location.href = result.redirect;
        } else {
            throw new Error(result.error || "Generation failed.");
        }

    } catch (error) {
        console.error("API Error:", error);
        alert("Oops! Something went wrong: " + error.message);
    } finally {
        // Reset UI
        genBtn.disabled = false;
        loader.classList.add('d-none');
        promptInput.classList.remove('opacity-50');
    }
}

// Sidebar Toggle (Mobile Friendly)
document.addEventListener('DOMContentLoaded', () => {
    // Add logic to highlight active link based on current URL
    const currentPath = window.location.pathname;
    document.querySelectorAll('.list-group-item').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});