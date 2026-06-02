"""
Security utilities for email verification and password reset codes.
Includes code generation, hashing, validation, and expiration checking.
"""

import os
import random
import string
import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# Constants for code generation
CODE_LENGTH = 6
CODE_EXPIRATION_MINUTES = 10
PASSWORD_RESET_EXPIRATION_MINUTES = 30
MAX_VERIFICATION_ATTEMPTS = 5
MAX_RESET_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
RESET_RESEND_COOLDOWN_SECONDS = 60


def generate_verification_code() -> str:
    """
    Generate a 6-digit verification code.
    Returns a string of random digits.
    """
    return ''.join(random.choices(string.digits, k=CODE_LENGTH))


def hash_code(code: str) -> str:
    """
    Hash a verification/reset code using bcrypt.
    
    Args:
        code: The plain-text code to hash
        
    Returns:
        The bcrypt hash of the code
    """
    code_bytes = code.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(code_bytes, salt)
    return hashed_bytes.decode('utf-8')


def verify_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verify a plain-text code against its bcrypt hash.
    
    Args:
        plain_code: The code entered by the user
        hashed_code: The stored hashed code
        
    Returns:
        True if codes match, False otherwise
    """
    try:
        code_bytes = plain_code.encode('utf-8')
        hash_bytes = hashed_code.encode('utf-8')
        return bcrypt.checkpw(code_bytes, hash_bytes)
    except (ValueError, TypeError):
        return False


def get_verification_code_expiration() -> datetime:
    """
    Get the expiration datetime for an email verification code.
    
    Returns:
        A timezone-aware datetime object set to CODE_EXPIRATION_MINUTES from now
    """
    return datetime.now(timezone.utc) + timedelta(minutes=CODE_EXPIRATION_MINUTES)


def get_reset_code_expiration() -> datetime:
    """
    Get the expiration datetime for a password reset code.
    
    Returns:
        A timezone-aware datetime object set to PASSWORD_RESET_EXPIRATION_MINUTES from now
    """
    return datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRATION_MINUTES)


def _ensure_aware(dt: datetime) -> datetime:
    """Make a naive datetime timezone-aware (UTC) if it isn't already."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_code_expired(expires_at: datetime) -> bool:
    """
    Check if a code has expired.
    
    Args:
        expires_at: The expiration datetime of the code
        
    Returns:
        True if code is expired, False otherwise
    """
    if expires_at is None:
        return True
    expires_at = _ensure_aware(expires_at)
    return datetime.now(timezone.utc) > expires_at


def can_resend_code(last_sent_at: datetime) -> bool:
    """
    Check if enough time has passed since the last code was sent.
    Used for rate limiting resend requests.
    
    Args:
        last_sent_at: The datetime when the last code was sent
        
    Returns:
        True if resend is allowed, False if still in cooldown
    """
    if last_sent_at is None:
        return True
    last_sent_at = _ensure_aware(last_sent_at)
    time_since_last = (datetime.now(timezone.utc) - last_sent_at).total_seconds()
    return time_since_last >= RESEND_COOLDOWN_SECONDS


def can_resend_reset_code(last_sent_at: datetime) -> bool:
    """
    Check if enough time has passed since the last reset code was sent.
    Used for rate limiting forgot-password requests.
    
    Args:
        last_sent_at: The datetime when the last reset code was sent
        
    Returns:
        True if resend is allowed, False if still in cooldown
    """
    if last_sent_at is None:
        return True
    last_sent_at = _ensure_aware(last_sent_at)
    time_since_last = (datetime.now(timezone.utc) - last_sent_at).total_seconds()
    return time_since_last >= RESET_RESEND_COOLDOWN_SECONDS


def get_seconds_until_resend_allowed(last_sent_at: datetime, cooldown_seconds: int = RESEND_COOLDOWN_SECONDS) -> int:
    """
    Get the number of seconds remaining until a resend is allowed.
    
    Args:
        last_sent_at: The datetime when the last code was sent
        cooldown_seconds: The cooldown period to use
        
    Returns:
        Number of seconds to wait, or 0 if resend is allowed
    """
    if last_sent_at is None:
        return 0
    last_sent_at = _ensure_aware(last_sent_at)
    time_since_last = (datetime.now(timezone.utc) - last_sent_at).total_seconds()
    remaining = cooldown_seconds - int(time_since_last)
    return max(0, remaining)


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    
    Args:
        password: The password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is strong"
