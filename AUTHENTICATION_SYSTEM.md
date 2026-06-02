# Email Authentication System Documentation

## Overview

This authentication system provides:
- **Email Verification** (OTP-style 6-digit codes) after signup
- **Forgot Password** with 6-digit reset codes
- **Password Reset** with validation and hashing
- **Rate Limiting** on code requests
- **Attempt Limiting** on wrong code submissions
- **Hashed Code Storage** for security
- **Timezone-Aware** datetimes

## Architecture

### Database Schema

The `User` model has been extended with the following fields:

```python
# Email Verification Fields
is_verified: Boolean              # Account verification status
email_verification_code_hash: String   # Hashed verification code
email_verification_expires_at: DateTime  # Code expiration time
email_verification_attempts: Integer  # Failed verification attempts
last_verification_sent_at: DateTime    # Rate limiting

# Password Reset Fields
password_reset_code_hash: String   # Hashed reset code
password_reset_expires_at: DateTime   # Code expiration time
password_reset_attempts: Integer   # Failed reset attempts
last_reset_sent_at: DateTime      # Rate limiting
```

### Expiration Times

- **Email Verification Code**: 10 minutes
- **Password Reset Code**: 30 minutes
- **Rate Limit Cooldown**: 60 seconds between resend/forgot-password requests

### Attempt Limits

- **Verification Attempts**: 5 incorrect codes per code generation
- **Reset Attempts**: 5 incorrect codes per code generation

## API Endpoints

### 1. Register (POST /auth/register)

**Request:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "student"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "student",
  "is_verified": false,
  "profile_picture": null,
  "created_at": "2024-01-15T10:30:00+00:00"
}
```

**Behavior:**
- Creates account with `is_verified = false`
- Generates 6-digit verification code
- Sends code via email (asynchronously)
- Code expires in 10 minutes
- Validates password strength:
  - At least 8 characters
  - Contains uppercase, lowercase, and digit

---

### 2. Verify Email (POST /auth/verify-email)

**Request:**
```json
{
  "email": "john@example.com",
  "code": "123456"
}
```

**Success Response (200):**
```json
{
  "message": "Email verified successfully",
  "success": true
}
```

**Error Responses:**
```json
{
  "message": "Verification code has expired. Please request a new one.",
  "success": false
}
```

```json
{
  "message": "Invalid verification code",
  "success": false
}
```

```json
{
  "message": "Too many incorrect attempts. Please request a new code.",
  "success": false
}
```

**Behavior:**
- Validates code format (6 digits)
- Checks code expiration
- Enforces attempt limit (5 attempts max)
- Invalidates code after successful verification
- Resets attempt counter after success

---

### 3. Resend Verification Code (POST /auth/resend-verification-code)

**Request:**
```json
{
  "email": "john@example.com"
}
```

**Response (200):**
```json
{
  "message": "Verification code sent successfully",
  "success": true
}
```

**Rate Limit Response:**
```json
{
  "message": "Please wait 45 seconds before requesting another code",
  "success": false
}
```

**Behavior:**
- Rate limited: 1 code per 60 seconds
- Only for unverified accounts
- Generates new code
- Resets attempt counter
- Does not reveal if email exists (generic success message)

---

### 4. Forgot Password (POST /auth/forgot-password)

**Request:**
```json
{
  "email": "john@example.com"
}
```

**Response (200):**
```json
{
  "message": "If the account exists, a password reset code has been sent",
  "success": true
}
```

**Behavior:**
- Always returns generic success (doesn't reveal if account exists)
- Rate limited: 1 reset per 60 seconds
- Generates 6-digit reset code
- Code expires in 30 minutes
- Resets attempt counter
- Sends code via email asynchronously

---

### 5. Reset Password (POST /auth/reset-password)

**Request:**
```json
{
  "email": "john@example.com",
  "reset_code": "654321",
  "new_password": "NewSecurePass456",
  "confirm_password": "NewSecurePass456"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully",
  "success": true
}
```

**Error Responses:**
```json
{
  "message": "Password reset code has expired",
  "success": false
}
```

```json
{
  "message": "Invalid reset code",
  "success": false
}
```

```json
{
  "message": "Passwords do not match",
  "success": false
}
```

```json
{
  "message": "Password must be at least 8 characters long",
  "success": false
}
```

**Behavior:**
- Validates reset code and expiration
- Enforces attempt limit (5 attempts max)
- Validates password strength (same as registration)
- Checks passwords match
- Hashes password securely (bcrypt)
- Invalidates code after successful reset
- Clears reset code fields

---

### 6. Login (POST /auth/login)

**Request:**
```json
{
  "username": "john@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "student"
}
```

**Note:** Email verification is currently optional for login. To enforce it, uncomment the verification check in the endpoint.

---

### 7. Get Current User (GET /auth/me)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "student",
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00+00:00"
}
```

---

## Frontend Integration Flow

### Signup + Email Verification Flow

```
User Signup Page
    ↓
[POST /auth/register]
    ↓
Success → Navigate to "Enter Verification Code" page
    ↓
User enters 6-digit code
    ↓
[POST /auth/verify-email]
    ↓
Success → "Email verified! You can now log in."
    ↓
Navigation to Login page
```

**Step-by-step Frontend Code Example:**

```javascript
// Step 1: Register
async function signup(fullName, email, password, role) {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_name: fullName,
      email: email,
      password: password,
      role: role
    })
  });
  
  if (response.ok) {
    // Show verification code input screen
    showVerificationScreen(email);
    return true;
  } else {
    const error = await response.json();
    showError(error.detail);
    return false;
  }
}

// Step 2: Verify Email
async function verifyEmail(email, code) {
  const response = await fetch('http://localhost:8000/auth/verify-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: email,
      code: code
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    showMessage('Email verified successfully!');
    navigateToLogin();
  } else {
    showError(result.message);
  }
  
  return result.success;
}

// Step 3 (Optional): Resend Code
async function resendVerificationCode(email) {
  const response = await fetch('http://localhost:8000/auth/resend-verification-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: email
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    showMessage('Code sent to your email');
  } else {
    showError(result.message);
  }
  
  return result.success;
}
```

---

### Forgot Password + Reset Flow

```
Login Page → "Forgot Password" link
    ↓
Enter Email Page
    ↓
[POST /auth/forgot-password]
    ↓
→ "Check your email for reset code"
    ↓
User enters 6-digit reset code
    ↓
Reset Password Page
    ↓
[POST /auth/reset-password]
    ↓
Success → "Password reset! Log in with new password"
    ↓
Navigation to Login page
```

**Step-by-step Frontend Code Example:**

```javascript
// Step 1: Request Password Reset
async function forgotPassword(email) {
  const response = await fetch('http://localhost:8000/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: email
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    showMessage('Check your email for the reset code');
    // Show reset code + password form
    showResetPasswordScreen(email);
  } else {
    showError(result.message);
  }
  
  return result.success;
}

// Step 2: Submit Reset Code and New Password
async function resetPassword(email, resetCode, newPassword, confirmPassword) {
  // Validate passwords match on frontend first
  if (newPassword !== confirmPassword) {
    showError('Passwords do not match');
    return false;
  }
  
  const response = await fetch('http://localhost:8000/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: email,
      reset_code: resetCode,
      new_password: newPassword,
      confirm_password: confirmPassword
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    showMessage('Password reset successfully!');
    navigateToLogin();
  } else {
    showError(result.message);
  }
  
  return result.success;
}
```

---

## Security Features

### 1. Code Hashing
- Codes are hashed using bcrypt before storage
- Plain codes are never stored in the database
- Codes are compared using bcrypt verification

### 2. Attempt Limiting
- Maximum 5 incorrect code attempts
- Attempt counter resets after successful verification
- After exceeding attempts, user must request a new code

### 3. Rate Limiting
- Resend verification code: 1 per 60 seconds
- Forgot password requests: 1 per 60 seconds
- Prevents abuse and account enumeration

### 4. Email Privacy
- Forgot password endpoint returns generic message
- Never reveals if account exists
- Resend endpoint also uses generic messaging

### 5. Password Strength
- Minimum 8 characters
- Must contain uppercase, lowercase, and digit
- Hashed using bcrypt with 12-round salt

### 6. Timezone-Aware Datetimes
- All timestamps use UTC timezone
- Expiration checks are timezone-safe
- Prevents timing-based attacks

---

## Configuration

### Environment Variables (.env)

```
DATABASE_URL=sqlite:///./devearn.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:3000
RESEND_API_KEY=re_your_api_key_here
MAIL_FROM=DevEarn <onboarding@resend.dev>
```

**For Production:**
- Use a strong, random `SECRET_KEY`
- Use production Resend credentials
- Change `MAIL_FROM` to your verified domain
- Update `FRONTEND_URL` to your production domain
- Use a production database (PostgreSQL recommended)

---

## Customization

### Change Code Length
Edit [app/services/auth.py](app/services/auth.py) line ~17:
```python
CODE_LENGTH = 6  # Change to desired length
```

### Change Expiration Times
Edit [app/services/auth.py](app/services/auth.py):
```python
CODE_EXPIRATION_MINUTES = 10           # Email verification code
PASSWORD_RESET_EXPIRATION_MINUTES = 30 # Reset code
RESEND_COOLDOWN_SECONDS = 60          # Rate limiting
```

### Change Attempt Limits
Edit [app/services/auth.py](app/services/auth.py):
```python
MAX_VERIFICATION_ATTEMPTS = 5  # Wrong code attempts
MAX_RESET_ATTEMPTS = 5         # Wrong reset code attempts
```

### Email Templates
Edit [app/services/email.py](app/services/email.py):
- Modify `send_verification_code_email()` for verification email
- Modify `send_password_reset_code_email()` for reset email

### Enforce Email Verification at Login
In [app/routers/auth.py](app/routers/auth.py), uncomment in `login()` function:
```python
if not user.is_verified:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Please verify your email before logging in"
    )
```

---

## Database Migration

### If Updating Existing Database

Run this to apply the User model changes:

```bash
# Using SQLAlchemy with Alembic (recommended)
alembic init alembic  # First time only
alembic revision --autogenerate -m "Add email verification fields"
alembic upgrade head

# Or manually with SQLite
# 1. Backup existing database
# 2. Delete devearn.db
# 3. Restart application (it will recreate with new schema)
```

---

## Testing the API

### Using cURL

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123",
    "role": "student"
  }'

# 2. Verify Email (replace CODE with actual code from email)
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'

# 3. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=test@example.com&password=TestPass123'
```

### Using Postman

1. Create a new collection "DevEarn Auth"
2. Add requests for each endpoint
3. Use the response from register to get email address
4. Check email service logs or mock service for the code
5. Use code in verify-email request

---

## Troubleshooting

### "RESEND_API_KEY is missing" Warning
- Check that `RESEND_API_KEY` is set in `.env`
- Restart the FastAPI application after updating `.env`
- Email will still be logged (for development)

### Code Expired Error
- Codes expire after 10 minutes for verification, 30 minutes for reset
- User must request a new code to proceed

### Too Many Attempts Error
- User has submitted 5 incorrect codes
- Must wait for new code via resend/forgot-password

### Rate Limit Error (Resend/Forgot Password)
- Must wait 60 seconds between requests
- Error message indicates seconds to wait

### Database Integrity Error
- Ensure `email` field is unique
- May need to recreate database if corrupted

---

## Files Modified/Created

### Created Files
- `app/services/auth.py` - Security utilities
- `app/services/email.py` - Email sending
- `app/services/__init__.py` - Package marker

### Modified Files
- `app/models.py` - Added verification/reset fields
- `app/schemas.py` - Added request/response schemas
- `app/routers/auth.py` - Complete rewrite with all endpoints
- `requirements.txt` - Added `requests` package
- `.env` - Cleaned up environment variables

---

## Support & Further Development

### Potential Enhancements
1. **SMS-based verification** - Add Twilio integration
2. **Social OAuth** - Google, GitHub login
3. **Session management** - Clear sessions on password reset
4. **Email change verification** - Verify before changing email
5. **Two-factor authentication** - TOTP/HOTP support
6. **Audit logging** - Track authentication events
7. **IP-based rate limiting** - Per IP/email limits

---

## License & Attribution

This authentication system is built for DevEarn and uses:
- FastAPI for the web framework
- SQLAlchemy for ORM
- Bcrypt for password hashing
- Resend for email delivery

---

**Documentation Last Updated:** January 2024
