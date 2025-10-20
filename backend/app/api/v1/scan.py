from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from ...middleware.auth_middleware import get_current_user
from app.middleware.site_middleware import verify_site_ownership
from app.schemas.site import ValidDomainSchema

router = APIRouter()
scan_router = router

@router.post("/test")
async def test_scan_domain(domain: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    await verify_site_ownership(domain, user, session)
    return {"success": True, "message": "Test scan endpoint hit.", "domain": domain.domain}
