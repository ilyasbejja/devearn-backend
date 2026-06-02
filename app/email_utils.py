import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "contact@devandearn.ma")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "DevEarn")

def send_verification_email(to_email: str, code: str):
    if not BREVO_API_KEY:
        print(f"[WARNING] BREVO_API_KEY is missing. Mock email sent to {to_email} with code: {code}")
        return False
        
    url = "https://api.brevo.com/v3/smtp/email"
    
    payload = {
        "sender": {
            "name": BREVO_SENDER_NAME,
            "email": BREVO_SENDER_EMAIL
        },
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": "Vérifiez votre compte DevEarn",
        "htmlContent": f"""
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; background-color: #f4f5fb; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                    <h2 style="color: #5A43F8; text-align: center;">Bienvenue sur DevEarn !</h2>
                    <p style="color: #334155; font-size: 16px; line-height: 1.5;">
                        Merci de vous être inscrit sur DevEarn. Pour activer votre compte et accéder à la plateforme, veuillez utiliser le code de vérification ci-dessous :
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="display: inline-block; padding: 15px 30px; background-color: rgba(90, 67, 248, 0.1); color: #5A43F8; font-size: 28px; font-weight: bold; letter-spacing: 5px; border-radius: 8px; border: 1px dashed #5A43F8;">
                            {code}
                        </span>
                    </div>
                    <p style="color: #334155; font-size: 14px; text-align: center;">
                        Si vous n'avez pas créé ce compte, vous pouvez ignorer cet email.
                    </p>
                </div>
            </body>
        </html>
        """
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = response.read()
            print(f"[INFO] Verification email sent to {to_email}. Response: {result}")
            return True
    except urllib.error.URLError as e:
        print(f"[ERROR] Failed to send email to {to_email}: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))
        return False
