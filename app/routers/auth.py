from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate, UserOut, Token, VerifyEmailRequest, 
    ResendVerificationCodeRequest, ForgotPasswordRequest, 
    ResetPasswordRequest, VerificationResponse, ForgotPasswordResponse, 
    ResetPasswordResponse
)
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.services.auth import (
    generate_verification_code,
    hash_code,
    verify_code,
    get_verification_code_expiration,
    get_reset_code_expiration,
    is_code_expired,
    can_resend_code,
    can_resend_reset_code,
    get_seconds_until_resend_allowed,
    is_password_strong,
    MAX_VERIFICATION_ATTEMPTS,
    MAX_RESET_ATTEMPTS,
)
from app.services.email import (
    send_verification_code_email,
    send_password_reset_code_email,
)

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - Creates account with is_verified = False
    - Generates and sends a 6-digit email verification code
    - Code expires in 10 minutes
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_strong, msg = is_password_strong(user.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Create new user marked as verified (email verification disabled)
    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        is_verified=True,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    
    return new_user


@router.post("/verify-email", response_model=VerificationResponse)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email with the code sent to the user.
    
    - Validates code format (6 digits)
    - Checks if code is correct and not expired
    - Marks user as verified
    - Invalidates the code after successful verification
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Generic response to not reveal if email exists
        return {
            "message": "If the account exists, verification code has been processed",
            "success": False
        }
    
    # Check if already verified
    if user.is_verified:
        return {
            "message": "Email is already verified",
            "success": True
        }
    
    # Check if user has a pending verification code
    if not user.email_verification_code_hash:
        return {
            "message": "No verification code found. Please register or request a new code.",
            "success": False
        }
    
    # Check if code is expired
    if is_code_expired(user.email_verification_expires_at):
        return {
            "message": "Verification code has expired. Please request a new one.",
            "success": False
        }
    
    # Check attempt limit
    if user.email_verification_attempts >= MAX_VERIFICATION_ATTEMPTS:
        return {
            "message": "Too many incorrect attempts. Please request a new code.",
            "success": False
        }
    
    # Verify the code
    if not verify_code(payload.code, user.email_verification_code_hash):
        user.email_verification_attempts += 1
        db.commit()
        return {
            "message": "Invalid verification code",
            "success": False
        }
    
    # Mark as verified and clear the code
    user.is_verified = True
    user.email_verification_code_hash = None
    user.email_verification_expires_at = None
    user.email_verification_attempts = 0
    db.commit()
    
    return {
        "message": "Email verified successfully",
        "success": True
    }


@router.post("/resend-verification-code", response_model=VerificationResponse)
def resend_verification_code(
    payload: ResendVerificationCodeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend verification code to user's email.
    
    - Rate limited to once per minute
    - Only for unverified users
    - Generates new code and resets attempt counter
    """
    user = db.query(User).filter(User.email == payload.email).first()
    
    # Generic response to not reveal if email exists
    if not user:
        return {
            "message": "If the account exists, verification code has been sent",
            "success": True
        }
    
    # Check if already verified
    if user.is_verified:
        return {
            "message": "Email is already verified",
            "success": True
        }
    
    # Check rate limiting
    if not can_resend_code(user.last_verification_sent_at):
        seconds_left = get_seconds_until_resend_allowed(user.last_verification_sent_at)
        return {
            "message": f"Please wait {seconds_left} seconds before requesting another code",
            "success": False
        }
    
    # Generate new verification code
    verification_code = generate_verification_code()
    hashed_code = hash_code(verification_code)
    code_expires_at = get_verification_code_expiration()
    
    # Update user with new code
    user.email_verification_code_hash = hashed_code
    user.email_verification_expires_at = code_expires_at
    user.email_verification_attempts = 0  # Reset attempts
    user.last_verification_sent_at = datetime.now(timezone.utc)
    db.commit()
    
    # Send email asynchronously
    background_tasks.add_task(
        send_verification_code_email,
        to_email=user.email,
        code=verification_code
    )
    
    return {
        "message": "Verification code sent successfully",
        "success": True
    }


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset code.
    
    - Always returns generic success message (doesn't reveal if account exists)
    - Rate limited to once per minute
    - Generates 6-digit reset code with 30-minute expiration
    """
    user = db.query(User).filter(User.email == payload.email).first()
    
    # Generic response to not reveal if email exists
    if not user:
        return {
            "message": "If the account exists, a password reset code has been sent",
            "success": True
        }
    
    # Check rate limiting
    if not can_resend_reset_code(user.last_reset_sent_at):
        seconds_left = get_seconds_until_resend_allowed(user.last_reset_sent_at)
        return {
            "message": f"Please wait {seconds_left} seconds before requesting another reset code",
            "success": True  # Still generic to not reveal timing info
        }
    
    # Generate reset code
    reset_code = generate_verification_code()
    hashed_code = hash_code(reset_code)
    code_expires_at = get_reset_code_expiration()
    
    # Update user with reset code
    user.password_reset_code_hash = hashed_code
    user.password_reset_expires_at = code_expires_at
    user.password_reset_attempts = 0  # Reset attempts
    user.last_reset_sent_at = datetime.now(timezone.utc)
    db.commit()
    
    # Send email asynchronously
    background_tasks.add_task(
        send_password_reset_code_email,
        to_email=user.email,
        code=reset_code
    )
    
    return {
        "message": "If the account exists, a password reset code has been sent",
        "success": True
    }


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset user password with reset code.
    
    - Validates reset code and expiration
    - Validates password strength
    - Passwords must match
    - Invalidates code after successful reset
    """
    user = db.query(User).filter(User.email == payload.email).first()
    
    if not user:
        return {
            "message": "Invalid reset request",
            "success": False
        }
    
    # Check if reset code exists
    if not user.password_reset_code_hash:
        return {
            "message": "No password reset code found",
            "success": False
        }
    
    # Check if code is expired
    if is_code_expired(user.password_reset_expires_at):
        user.password_reset_code_hash = None
        user.password_reset_expires_at = None
        db.commit()
        return {
            "message": "Password reset code has expired",
            "success": False
        }
    
    # Check attempt limit
    if user.password_reset_attempts >= MAX_RESET_ATTEMPTS:
        return {
            "message": "Too many incorrect attempts. Please request a new code.",
            "success": False
        }
    
    # Verify reset code
    if not verify_code(payload.reset_code, user.password_reset_code_hash):
        user.password_reset_attempts += 1
        db.commit()
        return {
            "message": "Invalid reset code",
            "success": False
        }
    
    # Check passwords match
    if payload.new_password != payload.confirm_password:
        return {
            "message": "Passwords do not match",
            "success": False
        }
    
    # Validate password strength
    is_strong, msg = is_password_strong(payload.new_password)
    if not is_strong:
        return {
            "message": msg,
            "success": False
        }
    
    # Update password and clear reset code
    user.hashed_password = get_password_hash(payload.new_password)
    user.password_reset_code_hash = None
    user.password_reset_expires_at = None
    user.password_reset_attempts = 0
    db.commit()
    
    return {
        "message": "Password reset successfully",
        "success": True
    }


@router.post("/login", response_model=Token)
def login(
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint.
    
    - Authenticates user with email and password
    - Returns JWT token
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Email verification disabled: allow login for all authenticated users
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    """
    return current_user
