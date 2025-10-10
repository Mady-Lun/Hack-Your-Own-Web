from ..core.config import Config
from datetime import datetime, timedelta
import jwt
import secrets
from ..models.user import RefreshToken


async def generate_tokens(response, user_data: dict, session):
    access_token_payload = {}
    access_token_payload['user'] = user_data
    access_token_payload['exp'] = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)  # Token expires in 30 minutes

    access_token = jwt.encode(
        payload=access_token_payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

    refresh_token = secrets.token_hex(40)
    expires_at = datetime.utcnow() + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS) # Token expires in 18 days

    new_token = RefreshToken(
        token = refresh_token,
        user_id = int(user_data['id']),
        expires_at = expires_at
    )
    session.add(new_token)
    await session.commit()

    # Set cookies
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=True if Config.ENV == "production" else False,  # set conditionally if ENV=prod
        samesite="none" if Config.ENV == "production" else "strict",  # or "strict" if local
        max_age=Config.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # in seconds
    )

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=True if Config.ENV == "production" else False,  # set conditionally if ENV=prod
        samesite="none" if Config.ENV == "production" else "strict",  # or "strict" if local
        max_age=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
    )

    return {"accessToken": access_token, "refreshToken": refresh_token}


async def generate_verification_token(response, user_data: dict, key: str = "verificationToken", expire_minutes: int = 3):
    token_payload = {}
    token_payload['user'] = user_data
    token_payload['exp'] = datetime.utcnow() + timedelta(minutes=expire_minutes)

    verification_token = jwt.encode(
        payload=token_payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

    response.set_cookie(
        key=key,
        value=verification_token,
        httponly=True,
        secure=True if Config.ENV == "production" else False,  # set conditionally if ENV=prod
        samesite="none" if Config.ENV == "production" else "strict",  # or "strict" if local
        max_age= expire_minutes * 60,  # in seconds
    )

    return verification_token
    