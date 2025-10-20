"""
Scanner Instance Manager

This module provides a singleton pattern for managing ZAPScanner instances
across Celery worker tasks. By reusing a single scanner instance, we improve
resource efficiency and reduce overhead.
"""

from typing import Optional
from app.services.zap_scanner import ZAPScanner


class ScannerInstanceManager:
    """
    Manages a singleton ZAPScanner instance for the worker process.
    This allows reusing the same scanner instance across multiple scan tasks,
    which is more efficient for resource management.
    """
    _instance: Optional[ZAPScanner] = None

    @classmethod
    def get_scanner(cls) -> ZAPScanner:
        """
        Get or create the shared scanner instance.
        Note: Each scan task will still call start_zap_instance() and stop_zap_instance()
        as needed for their specific scan operations.
        """
        if cls._instance is None:
            cls._instance = ZAPScanner()
        return cls._instance

    @classmethod
    def reset_scanner(cls) -> None:
        """
        Reset the scanner instance (useful for cleanup or error recovery).
        """
        if cls._instance is not None:
            try:
                cls._instance.stop_zap_instance()
            except Exception:
                pass  # Ignore errors during cleanup
            cls._instance = None


# Expose the scanner instance for use in tasks
scanner_manager = ScannerInstanceManager()
