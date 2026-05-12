function validateEmail() {
    return validatePassword();
}

function validatePassword() {
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    const passwordError = document.getElementById('passwordError');

    if (passwordField.value !== confirmPasswordField.value) {
        passwordError.textContent = 'Passwords do not match.';
        return false;
    } else {
        passwordError.textContent = ''; // Clear any previous error message
    }

    return true;
}
