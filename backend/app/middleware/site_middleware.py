from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.future import select
from app.core.db import get_session
from app.middleware.auth_middleware import get_current_user
from app.models.site import Site
from app.utils.logger import logger
import dns.resolver
from app.core.config import AppConfig

async def verify_site_ownership(domain, user, session, PREFIX: str = AppConfig.DOMAIN_VERIFICATION_TOKEN_PREFIX):
    logger.info(f"Verifying site ownership for user id: {user.id}")
    try:
        result = await session.execute(
            select(Site).where(
                Site.user_id == user.id,
                Site.domain == domain.domain,
                Site.is_verified == True
            )
        )
        site = result.scalars().first()

        if not site:
            logger.error(f"Site ownership verification failed for user id: {user.id} and domain: {domain.domain}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this site or it is not verified.")

        resolver = dns.resolver.Resolver()
        resolver.cache = None
        resolver.nameservers = ["1.1.1.1", "8.8.8.8"]
        resolver.timeout = 3
        resolver.lifetime = 5

        answers = resolver.resolve(domain.domain, 'TXT')

        for rdata in answers:
            txt = "".join([s.decode() if isinstance(s, bytes) else str(s) for s in rdata.strings]).strip().strip('"')
            # logger.info(f"Found TXT record: {txt}")
            token_candidate = txt
            if token_candidate.startswith(PREFIX):
                token_candidate = token_candidate[len(PREFIX):]
            if site.verification_token == token_candidate:
                logger.info(f"Site ownership verified successfully for user id: {user.id} and domain: {domain.domain}")
                return True

        logger.error(f"Site ownership verification failed: verification token not found in DNS records for domain: {domain.domain}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Site ownership verification failed.")

    except dns.resolver.NoAnswer:
        raise HTTPException(status_code=400, detail="No TXT records found.")
