# Frontend Implementation Guide - Email Authentication

## Quick Start

### Base URL
```
http://localhost:8000/auth
```

### Content-Type
```
Content-Type: application/json
```

---

## Signup Flow

### 1️⃣ User Submits Signup Form

```javascript
// signup.js
async function handleSignup() {
  const fullName = document.getElementById('fullName').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const role = document.getElementById('role').value || 'student';
  
  try {
    const response = await fetch('/auth/register', {
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
      const user = await response.json();
      // ✅ Account created, show verification screen
      showVerificationScreen(email);
      localStorage.setItem('pendingEmail', email);
    } else {
      const error = await response.json();
      showError(error.detail || 'Registration failed');
    }
  } catch (error) {
    showError('Network error: ' + error.message);
  }
}
```

### 2️⃣ User Enters Verification Code

```javascript
// verify-email.js
async function handleVerifyEmail() {
  const email = localStorage.getItem('pendingEmail');
  const code = document.getElementById('verificationCode').value;
  
  if (!code || code.length !== 6 || !/^\d+$/.test(code)) {
    showError('Code must be 6 digits');
    return;
  }
  
  try {
    const response = await fetch('/auth/verify-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        code: code
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      showSuccess('✅ Email verified! You can now login.');
      localStorage.removeItem('pendingEmail');
      setTimeout(() => {
        window.location.href = '/login.html';
      }, 2000);
    } else {
      showError(result.message);
    }
  } catch (error) {
    showError('Verification failed: ' + error.message);
  }
}

// Resend code button
async function handleResendCode() {
  const email = localStorage.getItem('pendingEmail');
  
  try {
    const response = await fetch('/auth/resend-verification-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email })
    });
    
    const result = await response.json();
    
    if (result.success) {
      showSuccess('Code sent! Check your email.');
    } else {
      showError(result.message);
    }
  } catch (error) {
    showError('Error: ' + error.message);
  }
}
```

---

## Forgot Password Flow

### 1️⃣ User Requests Password Reset

```javascript
// forgot-password.js
async function handleForgotPassword() {
  const email = document.getElementById('email').value;
  
  if (!email) {
    showError('Please enter your email');
    return;
  }
  
  try {
    const response = await fetch('/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email })
    });
    
    const result = await response.json();
    
    // Always shows success message (for security)
    showMessage('✅ Check your email for reset code');
    localStorage.setItem('resetEmail', email);
    
    // Show reset code form
    showResetPasswordForm();
  } catch (error) {
    showError('Error: ' + error.message);
  }
}
```

### 2️⃣ User Submits Reset Code & New Password

```javascript
// reset-password.js
async function handleResetPassword() {
  const email = localStorage.getItem('resetEmail');
  const resetCode = document.getElementById('resetCode').value;
  const newPassword = document.getElementById('newPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;
  
  // Frontend validation
  if (!resetCode || resetCode.length !== 6 || !/^\d+$/.test(resetCode)) {
    showError('Code must be 6 digits');
    return;
  }
  
  if (newPassword !== confirmPassword) {
    showError('Passwords do not match');
    return;
  }
  
  if (newPassword.length < 8) {
    showError('Password must be at least 8 characters');
    return;
  }
  
  try {
    const response = await fetch('/auth/reset-password', {
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
      showSuccess('✅ Password reset successfully!');
      localStorage.removeItem('resetEmail');
      setTimeout(() => {
        window.location.href = '/login.html';
      }, 2000);
    } else {
      showError(result.message);
    }
  } catch (error) {
    showError('Error: ' + error.message);
  }
}
```

---

## Login (After Verification)

```javascript
// login.js - existing code should work as-is
async function handleLogin() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  
  try {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('role', data.role);
      window.location.href = '/dashboard.html';
    } else {
      const error = await response.json();
      showError(error.detail || 'Login failed');
    }
  } catch (error) {
    showError('Error: ' + error.message);
  }
}
```

---

## HTML Components

### Verification Code Input
```html
<!-- verify-email.html -->
<div class="auth-container">
  <h2>Verify Your Email</h2>
  <p>We sent a 6-digit code to your email</p>
  
  <input 
    type="text" 
    id="verificationCode" 
    placeholder="000000"
    maxlength="6"
    inputmode="numeric"
    class="code-input"
  >
  
  <button onclick="handleVerifyEmail()" class="btn-primary">
    Verify Email
  </button>
  
  <p class="text-small">
    Didn't receive the code?
    <button onclick="handleResendCode()" class="btn-link">
      Resend Code
    </button>
  </p>
  
  <div id="message" class="message"></div>
</div>

<style>
  .code-input {
    font-size: 32px;
    letter-spacing: 10px;
    text-align: center;
    width: 200px;
    padding: 10px;
    border: 2px solid #5a43f8;
    border-radius: 8px;
    font-family: monospace;
  }
</style>
```

### Forgot Password Form
```html
<!-- forgot-password.html -->
<div class="auth-container">
  <h2>Reset Your Password</h2>
  <p>Enter your email address to receive a reset code</p>
  
  <input 
    type="email" 
    id="email" 
    placeholder="your@email.com"
    class="form-input"
  >
  
  <button onclick="handleForgotPassword()" class="btn-primary">
    Send Reset Code
  </button>
  
  <a href="login.html" class="btn-link">Back to Login</a>
  
  <div id="message" class="message"></div>
</div>
```

### Reset Password Form
```html
<!-- reset-password.html (shown after step 1) -->
<div class="auth-container">
  <h2>Enter Reset Code & New Password</h2>
  
  <input 
    type="text" 
    id="resetCode" 
    placeholder="000000"
    maxlength="6"
    inputmode="numeric"
    class="code-input"
  >
  
  <input 
    type="password" 
    id="newPassword" 
    placeholder="New Password"
    class="form-input"
  >
  
  <input 
    type="password" 
    id="confirmPassword" 
    placeholder="Confirm Password"
    class="form-input"
  >
  
  <button onclick="handleResetPassword()" class="btn-primary">
    Reset Password
  </button>
  
  <div id="message" class="message"></div>
</div>
```

---

## Helper Functions

```javascript
// utils.js
function showMessage(text) {
  const messageEl = document.getElementById('message');
  messageEl.textContent = text;
  messageEl.className = 'message message-info';
  messageEl.style.display = 'block';
}

function showSuccess(text) {
  const messageEl = document.getElementById('message');
  messageEl.textContent = text;
  messageEl.className = 'message message-success';
  messageEl.style.display = 'block';
}

function showError(text) {
  const messageEl = document.getElementById('message');
  messageEl.textContent = '❌ ' + text;
  messageEl.className = 'message message-error';
  messageEl.style.display = 'block';
}

// Get stored token (for authenticated requests)
function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
}
```

---

## CSS Styling

```css
/* auth.css */
.code-input {
  font-size: 32px;
  letter-spacing: 8px;
  text-align: center;
  padding: 12px;
  border: 2px solid #5a43f8;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-weight: bold;
  width: 220px;
}

.code-input:focus {
  outline: none;
  border-color: #7c5cff;
  box-shadow: 0 0 8px rgba(90, 67, 248, 0.3);
}

.message {
  padding: 12px 16px;
  margin: 16px 0;
  border-radius: 6px;
  text-align: center;
  font-size: 14px;
  display: none;
}

.message-success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.message-info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}
```

---

## Validation Rules

### Password Requirements
- ✅ At least 8 characters
- ✅ Contains uppercase letter (A-Z)
- ✅ Contains lowercase letter (a-z)
- ✅ Contains digit (0-9)

### Code Format
- ✅ Exactly 6 digits (0-9)
- ✅ No letters or special characters

### Email Format
- ✅ Must be valid email format
- ✅ Used for verification & reset

---

## Error Handling

| Error | Action |
|-------|--------|
| "Email already registered" | Show: "This email is already registered" + Link to login |
| "Invalid verification code" | Show: "Code is incorrect. Try again." |
| "Verification code has expired" | Show: "Code expired. Click 'Resend Code'" |
| "Too many incorrect attempts" | Show: "Request new code" |
| "Please wait X seconds..." | Disable button for X seconds, then re-enable |
| "Network error" | Retry button + offline message |

---

## Security Tips for Frontend

1. **Don't log sensitive data** - Never console.log passwords/codes
2. **Clear localStorage on logout** - Remove token, email, role
3. **Use HTTPS in production** - Protect credentials in transit
4. **Validate passwords locally** - Improve UX before API call
5. **Show/hide password toggles** - Let users verify before submit
6. **Disable submit while loading** - Prevent double submissions
7. **Handle network timeouts** - Add timeout to fetch calls
8. **Sanitize error messages** - Don't expose internal API details

---

## Testing Checklist

- [ ] Signup with valid data creates unverified account
- [ ] Signup with weak password shows error
- [ ] Email verification with valid code marks account verified
- [ ] Email verification with wrong code shows error
- [ ] After 5 wrong attempts, code request required
- [ ] Resend code works and resets attempts
- [ ] Forgot password accepts any email (no error reveal)
- [ ] Reset password validates code and password
- [ ] Login works after email verification
- [ ] Invalid token returns 401 error
- [ ] Rate limiting prevents abuse

---

## API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Resource created (register) |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (bad credentials) |
| 403 | Forbidden (unverified, etc) |
| 404 | Not found |
| 500 | Server error |

---

## Example Integration (Complete Signup Component)

```javascript
// signup-component.js
class SignupComponent {
  constructor() {
    this.step = 'form'; // 'form' or 'verification'
    this.email = null;
    this.setupEventListeners();
  }

  setupEventListeners() {
    document.getElementById('signupForm')?.addEventListener('submit', 
      (e) => this.handleSubmit(e)
    );
    document.getElementById('verifyBtn')?.addEventListener('click',
      () => this.handleVerify()
    );
    document.getElementById('resendBtn')?.addEventListener('click',
      () => this.handleResend()
    );
  }

  async handleSubmit(e) {
    e.preventDefault();
    
    const data = {
      full_name: document.getElementById('fullName').value,
      email: document.getElementById('email').value,
      password: document.getElementById('password').value,
      role: document.getElementById('role').value || 'student'
    };
    
    try {
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (response.ok) {
        this.email = data.email;
        this.showVerificationStep();
      } else {
        const error = await response.json();
        this.showError(error.detail);
      }
    } catch (error) {
      this.showError('Registration failed: ' + error.message);
    }
  }

  async handleVerify() {
    const code = document.getElementById('verificationCode').value;
    
    if (!/^\d{6}$/.test(code)) {
      this.showError('Code must be 6 digits');
      return;
    }
    
    try {
      const response = await fetch('/auth/verify-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: this.email,
          code: code
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        this.showSuccess('Email verified!');
        setTimeout(() => {
          window.location.href = '/login.html';
        }, 2000);
      } else {
        this.showError(result.message);
      }
    } catch (error) {
      this.showError('Verification failed: ' + error.message);
    }
  }

  async handleResend() {
    try {
      const response = await fetch('/auth/resend-verification-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: this.email })
      });
      
      const result = await response.json();
      this.showSuccess(result.message);
    } catch (error) {
      this.showError('Resend failed: ' + error.message);
    }
  }

  showVerificationStep() {
    document.getElementById('signupForm').style.display = 'none';
    document.getElementById('verificationForm').style.display = 'block';
    this.step = 'verification';
  }

  showError(msg) {
    const el = document.getElementById('message');
    el.textContent = '❌ ' + msg;
    el.className = 'message message-error';
  }

  showSuccess(msg) {
    const el = document.getElementById('message');
    el.textContent = '✅ ' + msg;
    el.className = 'message message-success';
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new SignupComponent();
});
```

---

## Deployment Notes

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if using Alembic)
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Production Checklist
- [ ] Use real RESEND_API_KEY
- [ ] Change SECRET_KEY to random value
- [ ] Update MAIL_FROM to verified domain
- [ ] Set FRONTEND_URL to production domain
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Set up email provider (Resend)
- [ ] Configure CORS for your domain
- [ ] Set up error logging
- [ ] Monitor rate limits

---

**Last Updated:** January 2024
