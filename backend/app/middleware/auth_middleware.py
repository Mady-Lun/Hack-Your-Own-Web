import jwt
from sqlalchemy import select
from app.models.user import User
from ..utils.logger import logger
from fastapi import HTTPException, status, Request, Depends
from app.core.db import get_session
from ..core.config import Config


async def validation_token(token: str):
    try:
        payload = jwt.decode(
            jwt = token, 
            key = Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )

        return payload
    
    except jwt.ExpiredSignatureError as e:
        logger.error(f"Token expired error: {e}")
        return {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        logger.error(f"Token invalid error: {e}")
        return {"error": "Invalid token"}
    except jwt.PYJWTError as e:
        logger.error(f"Token decoding error: {e}")
        return {"error": "Invalid token"}


async def get_current_user(request: Request, session = Depends(get_session)):
    token = request.cookies.get("accessToken")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    payload = await validation_token(token)
    if "error" in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=payload["error"])
    
    user_id = payload.get("user", {}).get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


def verify_verification(cookie_name: str = "verificationToken"):
    async def dependency(request: Request):
        token = request.cookies.get(cookie_name)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return await validation_token(token)
    return dependency