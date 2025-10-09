from app.core.config import AppConfig
from app.core.email import send_email

async def send_verification_email(email: str, user_name: str, verification_code: str):
    data = {
        'app_name': AppConfig.APP_NAME,
        'user_name': user_name,
        'verification_code': verification_code
    }

    subject = f"{verification_code} is your {AppConfig.APP_NAME} verification code"
    await send_email(
        recipients=[email],
        subject=subject,
        template_name="email_verification.html",
        context=data
    )