import datetime
from fastapi import HTTPException
from ..models.user import User
from ..core.security import get_password_hash, verify_password
from sqlmodel import select
from  ..utils.logger import logger
from fastapi.responses import JSONResponse
import random, string
from ..email.email import send_verification_email

async def register_user(data, session):
    logger.info("Account sign-up endpoint hit")
    try:
        existingUser = (await session.execute(select(User).where(User.email == data.email))).scalars().first()
        if existingUser:
            if existingUser.is_verified:
                logger.warning("Email already in use by a verified user")
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "User already exists"}
                )
            else:
                logger.warning("User already signup but not yet verified. Delete the existing user")
                await session.delete(existingUser)
                await session.commit()

        verification_code = ''.join(random.choices(string.digits, k=6))
        password_hash = await get_password_hash(data.password)

        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=password_hash,
            verification_code=verification_code,
            verification_code_expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=3),
        )
        session.add(user)
        await session.commit()
        # Combine first_name and last_name only if last_name exists
        user_name = f"{data.first_name} {data.last_name}" if data.last_name else data.first_name
        await send_verification_email(
            email=data.email,
            user_name=user_name,
            verification_code=verification_code
        )

        return JSONResponse(
            status_code=201,
            content={"success": True, "message": "User created successfully"}
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error"}
        )