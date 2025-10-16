from fastapi import APIRouter, status, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from app.core.db import get_session
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanDetailResponse,
    ScanListResponse,
    ScanStatsResponse,
)
from app.models.scan import ScanStatus, ScanType
from app.crud.scan import (
    create_scan_crud,
    get_scan_by_id_crud,
    get_user_scans_crud,
    delete_scan_crud,
    cancel_scan_crud,
    get_scan_stats_crud,
)
from app.middleware.auth_middleware import get_current_user
from fastapi.responses import JSONResponse


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_scan(
    data: ScanCreate,
    user_data=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new security scan

    - **target_url**: The URL to scan (must be http:// or https://)
    - **scan_type**: Type of scan:
        - **basic**: Passive scan (spider + passive scan) - No domain verification required
        - **full**: Active scan (spider + passive + active scan) - Requires domain ownership verification
    - **scan_config**: Optional configuration options

    Returns:
    - **201**: Scan created and queued successfully
    - **400**: Invalid scan type or URL
    - **401**: Unauthorized
    - **500**: Internal server error
    """
    user_id = int(user_data['user']['id'])
    return await create_scan_crud(data, user_id, session)


@router.get("/", response_model=ScanListResponse)
async def get_scans(
    status_filter: Optional[ScanStatus] = Query(None, alias="status"),
    scan_type: Optional[ScanType] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_data=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all scans for the authenticated user

    - **status**: Filter by scan status (optional)
    - **type**: Filter by scan type (optional)
    - **page**: Page number (default: 1)
    - **page_size**: Number of results per page (default: 20, max: 100)
    """
    user_id = int(user_data['user']['id'])
    scans, total = await get_user_scans_crud(
        user_id, session, status_filter, scan_type, page, page_size
    )

    return ScanListResponse(
        scans=[ScanResponse.model_validate(scan) for scan in scans],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=ScanStatsResponse)
async def get_scan_stats(
    user_data=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get scan statistics for the authenticated user

    Returns summary of:
    - Total scans by status
    - Total vulnerabilities found
    - Vulnerabilities by risk level
    """
    user_id = int(user_data['user']['id'])
    stats = await get_scan_stats_crud(user_id, session)
    return ScanStatsResponse(**stats)


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: int,
    user_data=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a specific scan including all alerts

    - **scan_id**: The ID of the scan
    """
    user_id = int(user_data['user']['id'])
    scan = await get_scan_by_id_crud(scan_id, user_id, session, include_alerts=True)

    if not scan:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Scan not found"}
        )

    return ScanDetailResponse.model_validate(scan)


@router.delete("/{scan_id}", status_code=status.HTTP_200_OK)
async def delete_scan(
    scan_id: int,
    user_data=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a scan and all its alerts

    - **scan_id**: The ID of the scan
    - Cannot delete scans that are currently in progress (cancel first)
    """
    user_id = int(user_data['user']['id'])
    return await delete_scan_crud(scan_id, user_id, session)


@router.post("/{scan_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_scan(
    scan_id: int,
    user_data=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Cancel a running or pending scan

    - **scan_id**: The ID of the scan
    - Only pending or in-progress scans can be cancelled
    """
    user_id = int(user_data['user']['id'])
    return await cancel_scan_crud(scan_id, user_id, session)


scan_router = router
