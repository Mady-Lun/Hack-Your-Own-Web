from celery import Task
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.celery_app import celery_app
from app.services.zap_scanner import ZAPScanner
from app.models.scan import Scan, ScanAlert, ScanStatus, ScanType, RiskLevel
from app.core.db import AsyncSessionLocal
from app.utils.logger import logger
from sqlalchemy import select
import asyncio


class ScanTask(Task):
    """Base task with error handling and cleanup"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure - just log, don't try to update DB"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Don't try to update DB here as it causes connection conflicts
        # The scan will remain in IN_PROGRESS state and can be cleaned up separately


@celery_app.task(bind=True, base=ScanTask, name="app.tasks.scan_tasks.run_scan")
def run_scan(self, scan_id: int) -> Dict[str, Any]:
    """
    Execute a security scan using OWASP ZAP

    Args:
        scan_id: Database ID of the scan

    Returns:
        Dictionary with scan results summary
    """
    logger.info(f"Starting scan task for scan_id: {scan_id}")

    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run_scan_async(scan_id, self))
        return result
    finally:
        loop.close()


async def _run_scan_async(scan_id: int, task: Task) -> Dict[str, Any]:
    """Async implementation of scan execution"""
    logger.info(f"Starting async scan execution for scan {scan_id}")

    # Use a single session for the entire scan to avoid connection conflicts
    async with AsyncSessionLocal() as session:
        # Get scan details
        result = await session.execute(select(Scan).filter_by(id=scan_id))
        scan = result.scalar_one_or_none()

        if not scan:
            error_msg = f"Scan with id {scan_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate scan type
        if scan.scan_type not in [ScanType.BASIC, ScanType.FULL]:
            error_msg = f"Invalid scan type {scan.scan_type} for scan {scan_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Update scan status to in_progress
        scan.status = ScanStatus.IN_PROGRESS
        scan.started_at = datetime.utcnow()
        scan.celery_task_id = task.request.id
        session.add(scan)
        await session.commit()

        logger.info(f"Scan {scan_id} marked as IN_PROGRESS")

        try:
            # Initialize ZAP scanner
            scanner = ZAPScanner()

            # Progress callback - just log for now to avoid DB connection conflicts
            def update_progress(percentage: int, step: str):
                """Log scan progress - called from sync context within async execution"""
                logger.info(f"Scan {scan_id} progress: {percentage}% - {step}")

            # Run appropriate scan type
            alerts = []
            if scan.scan_type == ScanType.BASIC:
                logger.info(f"Running BASIC scan for scan {scan_id}")
                alerts = scanner.run_basic_scan(scan.target_url, progress_callback=update_progress)
            elif scan.scan_type == ScanType.FULL:
                logger.info(f"Running FULL scan for scan {scan_id}")
                alerts = scanner.run_full_scan(scan.target_url, progress_callback=update_progress)
            else:
                error_msg = f"Invalid scan type: {scan.scan_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Process and store alerts
            await _process_alerts(session, scan, alerts)

            # Update scan completion
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.progress_percentage = 100
            scan.current_step = "Completed"
            scan.updated_at = datetime.utcnow()
            session.add(scan)
            await session.commit()

            logger.info(f"Scan {scan_id} completed successfully with {scan.total_alerts} alerts")

            return {
                "scan_id": scan_id,
                "status": "completed",
                "total_alerts": scan.total_alerts,
                "high_risk": scan.high_risk_count,
                "medium_risk": scan.medium_risk_count,
                "low_risk": scan.low_risk_count,
            }

        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}")
            # Refresh the scan object to avoid detached instance errors
            await session.refresh(scan)
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            scan.updated_at = datetime.utcnow()
            session.add(scan)
            await session.commit()
            raise


async def _process_alerts(session, scan: Scan, alerts: list):
    """Process and store ZAP alerts in database"""

    risk_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "informational": 0,
    }

    for alert in alerts:
        # Map ZAP risk levels to our enum
        risk_mapping = {
            "3": RiskLevel.HIGH,
            "2": RiskLevel.MEDIUM,
            "1": RiskLevel.LOW,
            "0": RiskLevel.INFORMATIONAL,
            "High": RiskLevel.HIGH,
            "Medium": RiskLevel.MEDIUM,
            "Low": RiskLevel.LOW,
            "Informational": RiskLevel.INFORMATIONAL,
        }

        risk_str = str(alert.get("risk", "0"))
        risk_level = risk_mapping.get(risk_str, RiskLevel.INFORMATIONAL)

        # Count by risk level
        risk_counts[risk_level.value] += 1

        # Create alert record
        scan_alert = ScanAlert(
            scan_id=scan.id,
            alert_name=alert.get("alert", "Unknown Alert"),
            risk_level=risk_level,
            confidence=alert.get("confidence", "Unknown"),
            description=alert.get("description"),
            solution=alert.get("solution"),
            reference=alert.get("reference"),
            cwe_id=str(alert.get("cweid")) if alert.get("cweid") else None,
            wasc_id=str(alert.get("wascid")) if alert.get("wascid") else None,
            url=alert.get("url", ""),
            method=alert.get("method"),
            param=alert.get("param"),
            attack=alert.get("attack"),
            evidence=alert.get("evidence"),
            other_info=alert.get("other"),
            alert_tags=alert.get("tags"),
        )
        session.add(scan_alert)

    # Update scan summary
    scan.total_alerts = len(alerts)
    scan.high_risk_count = risk_counts["high"]
    scan.medium_risk_count = risk_counts["medium"]
    scan.low_risk_count = risk_counts["low"]
    scan.info_count = risk_counts["informational"]
    session.add(scan)


@celery_app.task(bind=True, base=ScanTask, name="app.tasks.scan_tasks.cancel_scan")
def cancel_scan(self, scan_id: int) -> Dict[str, Any]:
    """
    Cancel a running scan

    Args:
        scan_id: Database ID of the scan

    Returns:
        Dictionary with cancellation status
    """
    logger.info(f"Cancelling scan task for scan_id: {scan_id}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_cancel_scan_async(scan_id))
        return result
    finally:
        loop.close()


async def _cancel_scan_async(scan_id: int) -> Dict[str, Any]:
    """Async implementation of scan cancellation"""

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Scan).filter_by(id=scan_id))
        scan = result.scalar_one_or_none()

        if not scan:
            raise ValueError(f"Scan with id {scan_id} not found")

        if scan.status not in [ScanStatus.PENDING, ScanStatus.IN_PROGRESS]:
            return {
                "scan_id": scan_id,
                "status": "not_cancellable",
                "message": f"Scan is in {scan.status} state and cannot be cancelled"
            }

        # Revoke Celery task if it exists
        if scan.celery_task_id:
            celery_app.control.revoke(scan.celery_task_id, terminate=True)

        # Update scan status
        scan.status = ScanStatus.CANCELLED
        scan.completed_at = datetime.utcnow()
        scan.updated_at = datetime.utcnow()
        scan.error_message = "Scan cancelled by user"
        session.add(scan)
        await session.commit()

        logger.info(f"Scan {scan_id} cancelled successfully")

        return {
            "scan_id": scan_id,
            "status": "cancelled",
            "message": "Scan cancelled successfully"
        }
