document.addEventListener('DOMContentLoaded', () => {
    const configElement = document.getElementById('firebase-config');
    if (!configElement) return;

    const firebaseConfig = JSON.parse(configElement.textContent);
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    async function sendTokenToBackend(user) {
        const idToken = await user.getIdToken();
        const response = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken: idToken })
        });
        const data = await response.json();
        if (data.success) {
            window.location.href = data.redirect; // Redirects to Dashboard
        } else {
            alert("Login failed: " + data.error);
        }
    }

    // Handle Buttons (Google)
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('#googleSignIn, #googleSignUp');
        if (!btn) return;
        e.preventDefault();
        const provider = new firebase.auth.GoogleAuthProvider();
        try {
            const result = await auth.signInWithPopup(provider);
            await sendTokenToBackend(result.user);
        } catch (error) { alert(error.message); }
    });

    // Handle Manual Forms (Login & Signup)
    const authForm = document.querySelector('form');
    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = authForm.email.value;
            const password = authForm.password.value;
            const isSignup = !!document.getElementById('googleSignUp');

            try {
                let userCred;
                if (isSignup) {
                    const username = authForm.username.value;
                    userCred = await auth.createUserWithEmailAndPassword(email, password);
                    await userCred.user.updateProfile({ displayName: username });
                } else {
                    userCred = await auth.signInWithEmailAndPassword(email, password);
                }
                // Send the manual user token to Flask to start the session!
                await sendTokenToBackend(userCred.user);
            } catch (error) { alert(error.message); }
        });
    }
});

document.addEventListener('click', async (e) => {
    // If we clicked the logout link, let the browser handle it naturally
    if (e.target.closest('.logout')) return; 

    const btn = e.target.closest('#googleSignIn, #googleSignUp');
    if (!btn) return;
    
    e.preventDefault();
    // ... rest of your login logic
});