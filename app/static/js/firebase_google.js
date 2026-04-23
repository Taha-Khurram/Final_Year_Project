document.addEventListener('DOMContentLoaded', () => {
    const configElement = document.getElementById('firebase-config');
    if (!configElement) return;

    const firebaseConfig = JSON.parse(configElement.textContent);
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    // Validation functions
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function validatePassword(password) {
        const errors = [];
        if (password.length < 8) errors.push('At least 8 characters');
        if (/\s/.test(password)) errors.push('No spaces allowed');
        if (!/[A-Z]/.test(password)) errors.push('At least one uppercase letter');
        if (!/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;']/.test(password)) errors.push('At least one special character');
        return errors;
    }

    function showError(inputId, message) {
        const errorEl = document.getElementById(inputId + 'Error');
        const wrapperEl = document.getElementById(inputId)?.closest('.input-wrapper');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.add('show');
        }
        if (wrapperEl) {
            wrapperEl.classList.add('error');
            wrapperEl.classList.remove('success');
        }
    }

    function clearError(inputId) {
        const errorEl = document.getElementById(inputId + 'Error');
        const wrapperEl = document.getElementById(inputId)?.closest('.input-wrapper');
        if (errorEl) {
            errorEl.textContent = '';
            errorEl.classList.remove('show');
        }
        if (wrapperEl) {
            wrapperEl.classList.remove('error');
            wrapperEl.classList.add('success');
        }
    }

    function clearAllErrors() {
        ['username', 'email', 'password'].forEach(id => {
            const errorEl = document.getElementById(id + 'Error');
            const wrapperEl = document.getElementById(id)?.closest('.input-wrapper');
            if (errorEl) {
                errorEl.textContent = '';
                errorEl.classList.remove('show');
            }
            if (wrapperEl) {
                wrapperEl.classList.remove('error', 'success');
            }
        });
    }

    function validateSignupForm(username, email, password) {
        let isValid = true;
        clearAllErrors();

        // Username validation
        if (!username || username.trim() === '') {
            showError('username', 'Full name is required');
            isValid = false;
        } else {
            clearError('username');
        }

        // Email validation
        if (!email || email.trim() === '') {
            showError('email', 'Email is required');
            isValid = false;
        } else if (!validateEmail(email)) {
            showError('email', 'Please enter a valid email address');
            isValid = false;
        } else {
            clearError('email');
        }

        // Password validation
        if (!password || password === '') {
            showError('password', 'Password is required');
            isValid = false;
        } else {
            const passwordErrors = validatePassword(password);
            if (passwordErrors.length > 0) {
                showError('password', passwordErrors.join(', '));
                isValid = false;
            } else {
                clearError('password');
            }
        }

        return isValid;
    }

    async function sendTokenToBackend(user) {
        const idToken = await user.getIdToken();
        const response = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken: idToken })
        });
        const data = await response.json();
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            alert("Login failed: " + data.error);
        }
    }

    // Helper functions for loading state
    function setButtonLoading(btn, isLoading) {
        if (isLoading) {
            btn.disabled = true;
            btn.classList.add('loading');
        } else {
            btn.disabled = false;
            btn.classList.remove('loading');
        }
    }

    // Handle Buttons (Google)
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('#googleSignIn, #googleSignUp');
        if (!btn) return;
        e.preventDefault();
        const provider = new firebase.auth.GoogleAuthProvider();
        setButtonLoading(btn, true);
        try {
            const result = await auth.signInWithPopup(provider);
            await sendTokenToBackend(result.user);
        } catch (error) {
            setButtonLoading(btn, false);
            alert(error.message);
        }
    });

    // Handle Manual Forms (Login & Signup)
    const authForm = document.querySelector('form');
    if (authForm) {
        const submitBtn = authForm.querySelector('button[type="submit"]');

        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = authForm.email.value;
            const password = authForm.password.value;
            const isSignup = !!document.getElementById('googleSignUp');

            try {
                let userCred;
                if (isSignup) {
                    const username = authForm.username.value;

                    // Validate signup form
                    if (!validateSignupForm(username, email, password)) {
                        return;
                    }

                    setButtonLoading(submitBtn, true);
                    userCred = await auth.createUserWithEmailAndPassword(email, password);
                    await userCred.user.updateProfile({ displayName: username });
                } else {
                    setButtonLoading(submitBtn, true);
                    userCred = await auth.signInWithEmailAndPassword(email, password);
                }
                await sendTokenToBackend(userCred.user);
            } catch (error) {
                setButtonLoading(submitBtn, false);
                alert(error.message);
            }
        });

        // Real-time validation on blur for signup
        const isSignup = !!document.getElementById('googleSignUp');
        if (isSignup) {
            const usernameInput = document.getElementById('username');
            const emailInput = document.getElementById('email');
            const passwordInput = document.getElementById('password');

            if (usernameInput) {
                usernameInput.addEventListener('blur', () => {
                    if (!usernameInput.value.trim()) {
                        showError('username', 'Full name is required');
                    } else {
                        clearError('username');
                    }
                });
            }

            if (emailInput) {
                emailInput.addEventListener('blur', () => {
                    if (!emailInput.value.trim()) {
                        showError('email', 'Email is required');
                    } else if (!validateEmail(emailInput.value)) {
                        showError('email', 'Please enter a valid email address');
                    } else {
                        clearError('email');
                    }
                });
            }

            if (passwordInput) {
                passwordInput.addEventListener('blur', () => {
                    if (!passwordInput.value) {
                        showError('password', 'Password is required');
                    } else {
                        const errors = validatePassword(passwordInput.value);
                        if (errors.length > 0) {
                            showError('password', errors.join(', '));
                        } else {
                            clearError('password');
                        }
                    }
                });

                // Live feedback while typing password
                passwordInput.addEventListener('input', () => {
                    const errors = validatePassword(passwordInput.value);
                    if (passwordInput.value && errors.length > 0) {
                        showError('password', errors.join(', '));
                    } else if (passwordInput.value) {
                        clearError('password');
                    }
                });
            }
        }
    }
});

document.addEventListener('click', async (e) => {
    if (e.target.closest('.logout')) return;

    const btn = e.target.closest('#googleSignIn, #googleSignUp');
    if (!btn) return;

    e.preventDefault();
});