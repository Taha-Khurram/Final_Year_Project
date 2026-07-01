"""
Server-side validators for authentication.

These functions are the *trust boundary* for signup rules. The client-side
checks in ``app/static/js/firebase_google.js`` are only for UX -- anyone can
bypass the browser and POST a Firebase ID token directly to
``/api/auth/verify``, so the real enforcement must live here.
"""
import re

# Gmail (and its googlemail.com alias) are the only domains allowed to sign up.
ALLOWED_EMAIL_DOMAINS = ("gmail.com", "googlemail.com")

# Local part (before the @): ASCII letters/digits plus . + _ - , must start and
# end with an alphanumeric character. Consecutive dots are rejected separately.
_LOCAL_PART_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.+_\-]*[A-Za-z0-9])?$")

# Characters accepted as "special" for password strength (mirrors the client).
_SPECIAL_CHARS = set("!@#$%^&*(),.?\":{}|<>_-+=[]\\/`~;'")


def is_valid_gmail(email):
    """Return True only for a well-formed Gmail address.

    Rejects other providers, malformed addresses, and common spoofing tricks:
    ``user@gmail.com.evil.com``, ``user@sub.gmail.com``,
    ``user@gmail.com@evil.com``, unicode/homoglyph domains, embedded
    whitespace, and leading/trailing dots. The domain check is
    case-insensitive; ``user+tag@gmail.com`` (plus-addressing) is allowed.
    """
    if not email or not isinstance(email, str):
        return False

    # Reject control characters (newline, carriage-return, tab, etc.) anywhere.
    # They are never valid in an email and are a classic header-injection
    # vector, so we refuse them before trimming ordinary surrounding spaces.
    if any(ord(ch) < 32 for ch in email):
        return False

    email = email.strip()

    # Reject any remaining embedded whitespace (strip only handles the ends).
    if any(ch.isspace() for ch in email):
        return False

    # Must contain exactly one "@" so the domain can't be smuggled in.
    if email.count("@") != 1:
        return False

    local, _, domain = email.partition("@")

    if domain.lower() not in ALLOWED_EMAIL_DOMAINS:
        return False

    if not local or not _LOCAL_PART_RE.match(local):
        return False

    # Gmail does not allow consecutive dots in the local part.
    if ".." in local:
        return False

    return True


def validate_password(password):
    """Return a list of unmet password requirements (empty list == valid).

    Mirrors the client-side rules: 8+ chars, no spaces, at least one uppercase
    letter, and at least one special character.
    """
    errors = []

    if not isinstance(password, str) or len(password) < 8:
        errors.append("At least 8 characters")
    if isinstance(password, str) and any(ch.isspace() for ch in password):
        errors.append("No spaces allowed")
    if not isinstance(password, str) or not any(ch.isupper() for ch in password):
        errors.append("At least one uppercase letter")
    if not isinstance(password, str) or not any(ch in _SPECIAL_CHARS for ch in password):
        errors.append("At least one special character")

    return errors
