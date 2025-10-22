from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.db import get_session
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanDetailResponse,
    ScanFullDetailResponse,
    ScanListResponse,
    ScanStatsResponse,
)
from app.models.scan import ScanStatus, ScanType
from app.models.user import User
from app.crud.scan import (
    create_scan_crud,
    get_scan_by_id_crud,
    get_user_scans_crud,
    delete_scan_crud,
    cancel_scan_crud,
    get_scan_stats_crud,
    get_scan_report_json_crud,
    get_scan_report_frontend_json_crud,
    get_scan_report_categorized_crud,
)
from app.middleware.auth_middleware import get_current_user
from fastapi.responses import JSONResponse, Response
import json


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_scan(
    data: ScanCreate,
    user: User = Depends(get_current_user),
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
    return await create_scan_crud(data, user.id, session)  # type: ignore[arg-type]


@router.get("/", response_model=ScanListResponse)
async def get_scans(
    status_filter: Optional[ScanStatus] = Query(None, alias="status"),
    scan_type: Optional[ScanType] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all scans for the authenticated user

    - **status**: Filter by scan status (optional)
    - **type**: Filter by scan type (optional)
    - **page**: Page number (default: 1)
    - **page_size**: Number of results per page (default: 20, max: 100)
    """
    scans, total = await get_user_scans_crud(
        user.id, session, status_filter, scan_type, page, page_size  # type: ignore[arg-type]
    )

    return ScanListResponse(
        scans=[ScanResponse.model_validate(scan) for scan in scans],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=ScanStatsResponse)
async def get_scan_stats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get scan statistics for the authenticated user

    Returns summary of:
    - Total scans by status
    - Total vulnerabilities found
    - Vulnerabilities by risk level
    """
    stats = await get_scan_stats_crud(user.id, session)  # type: ignore[arg-type]
    return ScanStatsResponse(**stats)


@router.get("/{scan_id}")
async def get_scan(
    scan_id: int,
    detailed: bool = Query(False, description="Include full alert details (default: false for summary only)"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a specific scan including alerts

    - **scan_id**: The ID of the scan
    - **detailed**: If true, returns full alert details. If false (default), returns summary alerts only.

    Default response includes lightweight alert summaries (id, alert_name, risk_level, confidence, url, method, cwe_id, created_at).
    Use detailed=true to get full alert information including description, solution, references, etc.
    """
    scan = await get_scan_by_id_crud(scan_id, user.id, session, include_alerts=True)  # type: ignore[arg-type]

    if not scan:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Scan not found"}
        )

    if detailed:
        return ScanFullDetailResponse.model_validate(scan)
    else:
        return ScanDetailResponse.model_validate(scan)


@router.delete("/{scan_id}", status_code=status.HTTP_200_OK)
async def delete_scan(
    scan_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a scan and all its alerts

    - **scan_id**: The ID of the scan
    - Cannot delete scans that are currently in progress (cancel first)
    """
    return await delete_scan_crud(scan_id, user.id, session)  # type: ignore[arg-type]


@router.post("/{scan_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_scan(
    scan_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Cancel a running or pending scan

    - **scan_id**: The ID of the scan
    - Only pending or in-progress scans can be cancelled
    """
    return await cancel_scan_crud(scan_id, user.id, session)  # type: ignore[arg-type]


@router.get("/{scan_id}/report/json")
async def get_scan_report_json(
    scan_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Download scan report in ZAP JSON format

    - **scan_id**: The ID of the scan
    - Returns a JSON file in OWASP ZAP report format
    - Only available for completed scans
    - Works for both BASIC and FULL scan types

    The JSON format includes:
    - Program metadata (ZAP version, timestamp)
    - Site information (target URL, host, port, SSL)
    - Detailed alerts with instances (vulnerabilities found)
    - Risk levels, confidence ratings, CWE/WASC IDs
    - Full descriptions, solutions, and references
    """
    report = await get_scan_report_json_crud(scan_id, user.id, session)  # type: ignore[arg-type]

    if not report:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Scan not found or not completed"}
        )

    # Return as downloadable JSON file
    json_str = json.dumps(report, indent=2)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}_report.json"
        }
    )


@router.get("/{scan_id}/report/frontend")
async def get_scan_report_frontend(
    scan_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get scan report in frontend-optimized JSON format (RECOMMENDED for Web UIs)

    - **scan_id**: The ID of the scan
    - Returns JSON optimized for frontend frameworks (React, Vue, Angular)
    - Only available for completed scans
    - Works for both BASIC and FULL scan types

    This format is HIGHLY RECOMMENDED for frontend developers because it provides:
    - Clean, camelCase field names (JavaScript convention)
    - Pre-grouped alerts by risk level
    - Summary statistics ready for dashboards
    - ISO datetime formats
    - Flat alert structure (no complex nesting)
    - Easy filtering and sorting support
    - All data needed for visualization in one response

    Use this instead of /report/json if you're building a web frontend!
    """
    report = await get_scan_report_frontend_json_crud(scan_id, user.id, session)  # type: ignore[arg-type]

    if not report:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Scan not found or not completed"}
        )

    # Return as JSON (can be downloaded or consumed directly)
    return JSONResponse(content=report)


@router.get("/{scan_id}/report/categorized")
async def get_scan_report_categorized(
    scan_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get scan report with categorized vulnerabilities and pass/fail status (BEST for Users)

    - **scan_id**: The ID of the scan
    - Returns JSON with clear pass/fail status for each vulnerability type
    - Only available for completed scans
    - Works for both BASIC and FULL scan types

    This format is HIGHLY RECOMMENDED for users who want to:
    - Quickly understand if their website passed or failed security tests
    - See clear categorization of vulnerabilities:
      * SQL Injection (SQLi)
      * Cross-Site Scripting (XSS)
      * Security Headers
      * Open Redirects
    - Get actionable security insights with risk levels
    - Understand overall security posture at a glance

    Each vulnerability test shows:
    - Pass/Fail status
    - Number of issues (high/medium/low/informational)
    - Detailed list of specific vulnerabilities found
    - Solutions and references for remediation

    Perfect for security dashboards and reporting!
    """
    report = await get_scan_report_categorized_crud(scan_id, user.id, session)  # type: ignore[arg-type]

    if not report:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Scan not found or not completed"}
        )

    # Return as JSON
    return JSONResponse(content=report)


scan_router = router
