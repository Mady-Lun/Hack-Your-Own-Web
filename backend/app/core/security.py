from passlib.context import CryptContext
from .config import Config


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

async def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) 


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def revoke_session_token(response):
    response.set_cookie(
        key="accessToken",
        value="",  # empty value
        httponly=True,
        secure=True if Config.ENV == "production" else False,
        samesite="none" if Config.ENV == "production" else "strict",
        max_age=0,  # expire immediately
    )

    response.set_cookie(
        key="refreshToken",
        value="",  # empty value
        httponly=True,
        secure=True if Config.ENV == "production" else False,
        samesite="none" if Config.ENV == "production" else "strict",
        max_age=0,  # expire immediately
    )
    return True


async def revoke_token(response, key: str = "verificationToken"):
    response.set_cookie(
        key=key,
        value="",  # empty value
        httponly=True,
        secure=True if Config.ENV == "production" else False,
        samesite="none" if Config.ENV == "production" else "strict",
        max_age=0,  # expire immediately
    )
    return True
