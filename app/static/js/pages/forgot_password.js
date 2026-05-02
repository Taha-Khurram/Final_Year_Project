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

        auth.sendPasswordResetEmail(email)
            .then(function () {
                sentEmail.textContent = email;
                emailStep.style.display = 'none';
                successStep.style.display = 'block';
            })
            .catch(function (error) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');

                if (error.code === 'auth/user-not-found') {
                    emailError.textContent = 'No account found with this email address';
                } else if (error.code === 'auth/invalid-email') {
                    emailError.textContent = 'Please enter a valid email address';
                } else if (error.code === 'auth/too-many-requests') {
                    emailError.textContent = 'Too many attempts. Please try again later';
                } else {
                    emailError.textContent = 'Something went wrong. Please try again';
                }
                emailError.classList.add('show');
            });
    });
});
