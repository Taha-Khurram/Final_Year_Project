document.addEventListener('DOMContentLoaded', function () {
    var configElement = document.getElementById('firebase-config');
    if (!configElement) return;

    var firebaseConfig = JSON.parse(configElement.textContent);
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    var auth = firebase.auth();

    var resetForm = document.getElementById('resetForm');
    var emailStep = document.getElementById('emailStep');
    var successStep = document.getElementById('successStep');
    var sentEmail = document.getElementById('sentEmail');
    var emailError = document.getElementById('emailError');

    resetForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var email = document.getElementById('resetEmail').value.trim();

        emailError.textContent = '';
        emailError.classList.remove('show');

        if (!email) {
            emailError.textContent = 'Please enter your email address';
            emailError.classList.add('show');
            return;
        }

        var submitBtn = resetForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');

        fetch('/api/auth/check-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (result) {
            if (!result.ok || !result.data.exists) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
                emailError.textContent = result.data.error || 'No account found with this email address';
                emailError.classList.add('show');
                return;
            }

            auth.sendPasswordResetEmail(email)
                .then(function () {
                    sentEmail.textContent = email;
                    emailStep.style.display = 'none';
                    successStep.style.display = 'block';
                })
                .catch(function (error) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('loading');

                    if (error.code === 'auth/too-many-requests') {
                        emailError.textContent = 'Too many attempts. Please try again later';
                    } else {
                        emailError.textContent = 'Something went wrong. Please try again';
                    }
                    emailError.classList.add('show');
                });
        })
        .catch(function () {
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
            emailError.textContent = 'No email found, please check and try again';
            emailError.classList.add('show');
        });
    });
});
