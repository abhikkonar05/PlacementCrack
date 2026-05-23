import asyncio
import httpx
import logging
from datetime import datetime
from app.config import settings

logger = logging.getLogger("app.auth.email_service")

# Premium HTML Template for OTP Verification
OTP_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify Your Email</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background-color: #0f172a;
      color: #e2e8f0;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 550px;
      margin: 40px auto;
      background-color: #1e293b;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
      overflow: hidden;
      border: 1px solid #334155;
    }}
    .header {{
      background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
      padding: 40px 20px;
      text-align: center;
    }}
    .header h1 {{
      color: #ffffff;
      margin: 0;
      font-size: 30px;
      font-weight: 800;
      letter-spacing: -0.025em;
      text-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
    }}
    .header p {{
      color: rgba(255, 255, 255, 0.95);
      margin: 8px 0 0 0;
      font-size: 15px;
      font-weight: 500;
    }}
    .content {{
      padding: 40px 30px;
    }}
    .greeting {{
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 16px;
      color: #f8fafc;
    }}
    .message {{
      font-size: 15px;
      line-height: 1.6;
      color: #94a3b8;
      margin-bottom: 30px;
    }}
    .otp-container {{
      background-color: #312e81;
      border: 2px dashed #818cf8;
      border-radius: 12px;
      padding: 24px;
      text-align: center;
      margin-bottom: 30px;
      box-shadow: 0 4px 15px rgba(99, 102, 241, 0.1);
    }}
    .otp-code {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 40px;
      font-weight: 800;
      color: #a5b4fc;
      letter-spacing: 6px;
      margin: 0;
      text-shadow: 0 0 10px rgba(165, 180, 252, 0.3);
    }}
    .otp-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: #94a3b8;
      margin-top: 8px;
      font-weight: 600;
    }}
    .expiry-note {{
      font-size: 13px;
      color: #f87171;
      text-align: center;
      margin-bottom: 30px;
      font-weight: 500;
      background-color: rgba(248, 113, 113, 0.1);
      padding: 10px;
      border-radius: 8px;
      border: 1px solid rgba(248, 113, 113, 0.2);
    }}
    .footer {{
      background-color: #0f172a;
      padding: 24px;
      text-align: center;
      border-top: 1px solid #334155;
      font-size: 12px;
      color: #64748b;
    }}
    .branding {{
      font-size: 14px;
      color: #cbd5e1;
      font-weight: 600;
      margin-bottom: 6px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>PlacementCrack</h1>
      <p>Elevate Your Career Preparation</p>
    </div>
    <div class="content">
      <div class="greeting">Hello,</div>
      <div class="message">
        Thank you for choosing <strong>PlacementCrack</strong>! We are excited to support you on your placement journey. To complete your account verification, please enter the 6-digit OTP code below:
      </div>
      <div class="otp-container">
        <div class="otp-code">{otp}</div>
        <div class="otp-label">Verification OTP</div>
      </div>
      <div class="expiry-note">
        [Warning] This verification code is valid for exactly <strong>3 minutes</strong>. Do not share this OTP with anyone for security purposes.
      </div>
      <div class="message" style="margin-bottom: 0;">
        Ready to crack your next placement? Prepare with mock interviews, evaluate resumes, and solve coding challenges on PlacementCrack!
      </div>
    </div>
    <div class="footer">
      <div class="branding">PlacementCrack Team</div>
      <p>&copy; 2026 PlacementCrack. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

# Premium HTML Template for Unique Login Key (MFA)
LOGIN_KEY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Secure Login Key</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background-color: #0f172a;
      color: #e2e8f0;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 550px;
      margin: 40px auto;
      background-color: #1e293b;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
      overflow: hidden;
      border: 1px solid #334155;
    }}
    .header {{
      background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
      padding: 40px 20px;
      text-align: center;
    }}
    .header h1 {{
      color: #ffffff;
      margin: 0;
      font-size: 30px;
      font-weight: 800;
      letter-spacing: -0.025em;
      text-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
    }}
    .header p {{
      color: rgba(255, 255, 255, 0.95);
      margin: 8px 0 0 0;
      font-size: 15px;
      font-weight: 500;
    }}
    .content {{
      padding: 40px 30px;
    }}
    .greeting {{
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 16px;
      color: #f8fafc;
    }}
    .message {{
      font-size: 15px;
      line-height: 1.6;
      color: #94a3b8;
      margin-bottom: 30px;
    }}
    .key-container {{
      background-color: #064e3b;
      border: 2px dashed #34d399;
      border-radius: 12px;
      padding: 24px;
      text-align: center;
      margin-bottom: 30px;
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
    }}
    .login-key {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 44px;
      font-weight: 800;
      color: #a7f3d0;
      letter-spacing: 4px;
      margin: 0;
      text-shadow: 0 0 10px rgba(167, 243, 208, 0.3);
    }}
    .key-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: #34d399;
      margin-top: 8px;
      font-weight: 600;
    }}
    .details-box {{
      background-color: #0f172a;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 30px;
      font-size: 13px;
      border: 1px solid #334155;
      color: #94a3b8;
    }}
    .detail-item {{
      margin-bottom: 8px;
    }}
    .detail-item:last-child {{
      margin-bottom: 0;
    }}
    .detail-label {{
      font-weight: 600;
      color: #cbd5e1;
    }}
    .footer {{
      background-color: #0f172a;
      padding: 24px;
      text-align: center;
      border-top: 1px solid #334155;
      font-size: 12px;
      color: #64748b;
    }}
    .branding {{
      font-size: 14px;
      color: #cbd5e1;
      font-weight: 600;
      margin-bottom: 6px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>PlacementCrack Secure Entry</h1>
      <p>Multi-Factor Authentication Shield</p>
    </div>
    <div class="content">
      <div class="greeting">Hello {first_name},</div>
      <div class="message">
        A login attempt was initiated for your PlacementCrack account. To complete the login process, please use the following unique, single-use login key:
      </div>
      <div class="key-container">
        <div class="login-key">{login_key}</div>
        <div class="key-label">Unique Login Key</div>
      </div>
      <div class="details-box">
        <div class="detail-item"><span class="detail-label">Attempt Time:</span> {login_time}</div>
        <div class="detail-item"><span class="detail-label">Status:</span> Pending MFA Verification</div>
      </div>
      <div class="message" style="margin-bottom: 0; color: #ef4444; font-weight: 500; font-size: 13px;">
        [Security Note] If you did not initiate this login request, please change your password immediately and secure your account.
      </div>
    </div>
    <div class="footer">
      <div class="branding">PlacementCrack Security Shield</div>
      <p>&copy; 2026 PlacementCrack. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

def print_resend_dev_simulator(to_email: str, subject: str, code: str, mode: str):
    """Outputs a beautifully formatted terminal fallback for local Resend API testing."""
    mode_text = "EMAIL OTP CODE" if mode == "otp" else "MFA UNIQUE LOGIN KEY"
    print("\n" + "="*80)
    print(f" [DEV] RESEND API SIMULATOR - {mode_text}")
    print("="*80)
    print(f"  Recipient Email: {to_email}")
    print(f"  Subject Line   : {subject}")
    print(f"  Access Code    : {code}  (Expires in 3 minutes)")
    print("="*80 + "\n")

async def send_resend_email(to_email: str, subject: str, html_content: str) -> bool:
    """Helper method to send an email using the Resend REST API asynchronously."""
    if not settings.RESEND_API_KEY:
        return False
        
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Format the 'from' address dynamically based on settings
    from_address = settings.FROM_EMAIL
    if "@" in from_address and "<" not in from_address:
        from_address = f"PlacementCrack <{from_address}>"

    payload = {
        "from": from_address,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                logger.info(f"Resend email successfully sent to {to_email}")
                return True
            else:
                logger.error(f"Resend API error ({response.status_code}): {response.text}")
                return False
    except Exception as e:
        logger.error(f"Resend HTTP request failed: {e}")
        return False

async def send_otp_email(to_email: str, otp: str) -> bool:
    """Async method to dispatch a beautifully formatted OTP Verification Email."""
    subject = f"{otp} is your PlacementCrack verification code"
    html_content = OTP_HTML_TEMPLATE.format(otp=otp)

    # Attempt Resend call
    success = await send_resend_email(to_email, subject, html_content)
    
    # Dev mode terminal simulator fallback
    if not success or not settings.RESEND_API_KEY:
        print_resend_dev_simulator(to_email, subject, otp, "otp")
        return True
        
    return success

async def send_login_key_email(to_email: str, first_name: str, login_key: str) -> bool:
    """Async method to dispatch a beautifully formatted secure MFA Login Key Email."""
    subject = f"Secure login key {login_key} for PlacementCrack"
    login_time = datetime.now().strftime("%B %d, %Y, %I:%M %p")
    html_content = LOGIN_KEY_HTML_TEMPLATE.format(first_name=first_name, login_key=login_key, login_time=login_time)

    # Attempt Resend call
    success = await send_resend_email(to_email, subject, html_content)
    
    # Dev mode terminal simulator fallback
    if not success or not settings.RESEND_API_KEY:
        print_resend_dev_simulator(to_email, subject, login_key, "login_key")
        return True
        
    return success
