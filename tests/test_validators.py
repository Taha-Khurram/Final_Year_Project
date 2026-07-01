"""
Unit tests for the server-side signup validators.

Covers positive, negative, and security-focused cases for the Gmail-only rule
and the password-strength rule in ``app/utils/validators.py``.
"""
import pytest

from app.utils.validators import is_valid_gmail, validate_password


# --------------------------------------------------------------------------- #
# is_valid_gmail — POSITIVE cases
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("email", [
    "john@gmail.com",
    "john.doe@gmail.com",
    "john_doe@gmail.com",
    "john-doe@gmail.com",
    "john+newsletter@gmail.com",      # plus-addressing is legitimate
    "john123@gmail.com",
    "JohnDoe@gmail.com",              # local part case is preserved/allowed
    "john@GMAIL.COM",                 # domain match is case-insensitive
    "john@googlemail.com",            # official gmail alias
    "  john@gmail.com  ",             # surrounding whitespace is trimmed
])
def test_valid_gmail_accepted(email):
    assert is_valid_gmail(email) is True


# --------------------------------------------------------------------------- #
# is_valid_gmail — NEGATIVE cases (wrong provider / malformed)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("email", [
    "john@yahoo.com",
    "john@outlook.com",
    "john@hotmail.com",
    "john@company.co",
    "john@gmail.co",                  # not gmail.com
    "john@gmial.com",                 # typo domain
    "plainaddress",                   # no @
    "john@",                          # missing domain
    "@gmail.com",                     # missing local part
    "john@@gmail.com",                # empty middle
    "",                               # empty string
    "   ",                            # whitespace only
])
def test_invalid_email_rejected(email):
    assert is_valid_gmail(email) is False


@pytest.mark.parametrize("value", [None, 123, [], {}, True])
def test_non_string_rejected(value):
    assert is_valid_gmail(value) is False


# --------------------------------------------------------------------------- #
# is_valid_gmail — SECURITY cases (spoofing / injection tricks)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("email", [
    "john@gmail.com.evil.com",        # domain suffix spoof
    "john@sub.gmail.com",             # subdomain spoof
    "john@gmail.com@evil.com",        # two @, real domain is evil.com
    "john@evil.com?@gmail.com",       # confusion attempt
    "john@gmаil.com",                 # cyrillic 'а' homoglyph in domain
    "jоhn@gmail.com",                 # cyrillic 'о' homoglyph in local part
    "john@gmail.com\n",               # trailing newline (embedded whitespace)
    "john\t@gmail.com",               # embedded tab
    "john doe@gmail.com",             # embedded space
    ".john@gmail.com",                # local part starts with a dot
    "john.@gmail.com",                # local part ends with a dot
    "john..doe@gmail.com",            # consecutive dots
    "john@gmail.com/../admin",        # path-traversal-looking suffix
    "john@gmail.com%00@gmail.com",    # null-byte-ish injection
])
def test_spoofing_attempts_rejected(email):
    assert is_valid_gmail(email) is False


# --------------------------------------------------------------------------- #
# validate_password
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("password", [
    "Password1!",
    "Str0ng@Pass",
    "GoodP@ssword",
    "ABCdef12$",
])
def test_strong_passwords_pass(password):
    assert validate_password(password) == []


def test_password_too_short():
    assert "At least 8 characters" in validate_password("Ab1!")


def test_password_missing_uppercase():
    assert "At least one uppercase letter" in validate_password("password1!")


def test_password_missing_special_char():
    assert "At least one special character" in validate_password("Password12")


def test_password_with_spaces_rejected():
    errors = validate_password("Pass word1!")
    assert "No spaces allowed" in errors


def test_empty_password_reports_multiple_errors():
    errors = validate_password("")
    assert "At least 8 characters" in errors
    assert "At least one uppercase letter" in errors
    assert "At least one special character" in errors


@pytest.mark.parametrize("value", [None, 12345678, ["Password1!"]])
def test_password_non_string_is_invalid(value):
    # Non-strings must never be treated as valid passwords.
    assert validate_password(value) != []
