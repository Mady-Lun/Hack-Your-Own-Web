from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.middleware.auth_middleware import get_current_user
from app.middleware.site_middleware import verify_site_ownership
from app.schemas.site import ValidDomainSchema
from app.crud.site import domain_registry_crud, domain_verification_crud, get_domain_status_crud, get_list_user_domains_crud, remove_domain_crud


router = APIRouter()
site_router = router

@router.get("/")
async def get_list_user_domains(user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await get_list_user_domains_crud(user, session)

@router.post("/")
async def register_domain(data: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await domain_registry_crud(data, user, session)

@router.get("/status")
async def get_domain_status(domain: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await get_domain_status_crud(domain, user, session)

@router.post("/verify")
async def verify_domain(domain: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await domain_verification_crud(domain, user, session)

@router.delete("/")
async def remove_domain(domain: ValidDomainSchema, user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await remove_domain_crud(domain, user, session)
