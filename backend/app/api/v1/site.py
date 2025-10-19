from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.middleware.auth_middleware import get_current_user
from app.schemas.site import ValidDomainSchema
from app.crud.site import domain_registry_crud, domain_verification_crud, get_domain_status_crud


router = APIRouter()
site_router = router

@router.post("/")
async def register_domain(data: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await domain_registry_crud(data, user, session)

@router.get("/status")
async def get_domain_status(domain: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await get_domain_status_crud(domain, user, session)

@router.post("/verify")
async def verify_domain(domain: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await domain_verification_crud(domain, user, session)
