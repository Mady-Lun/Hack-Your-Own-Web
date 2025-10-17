import time
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from zapv2 import ZAPv2
import docker
from docker.errors import NotFound, APIError
from app.utils.logger import logger
from app.core.config import ZAPConfig

if TYPE_CHECKING:
    from docker.models.containers import Container


class ZAPScanner:
    """
    OWASP ZAP Scanner with Docker integration.
    Supports multiple scan types and provides progress tracking.
    """

    def __init__(
        self,
        zap_host: str = ZAPConfig.ZAP_HOST,
        zap_port: int = ZAPConfig.ZAP_PORT,
        zap_api_key: str = ZAPConfig.ZAP_API_KEY,
        use_docker: bool = ZAPConfig.USE_DOCKER_ZAP,
    ):
        self.zap_host = zap_host
        self.zap_port = zap_port
        self.zap_api_key = zap_api_key
        self.use_docker = use_docker
        self.docker_container: Optional["Container"] = None
        self.zap: Optional[ZAPv2] = None

    def _ensure_zap_initialized(self) -> ZAPv2:
        """Ensure ZAP instance is initialized, raise exception if not."""
        if self.zap is None:
            raise RuntimeError(
                "ZAP instance not initialized. Call start_zap_instance() first."
            )
        return self.zap

    def start_zap_instance(self) -> bool:
        """Start a ZAP instance (Docker or connect to existing)"""
        try:
            if self.use_docker:
                return self._start_docker_zap()
            else:
                # Connect to existing ZAP instance
                self.zap = ZAPv2(
                    apikey=self.zap_api_key,
                    proxies={
                        "http": f"http://{self.zap_host}:{self.zap_port}",
                        "https": f"http://{self.zap_host}:{self.zap_port}",
                    }
                )
                # Test connection
                self.zap.core.version
                logger.info(f"Connected to existing ZAP instance at {self.zap_host}:{self.zap_port}")
                return True
        except Exception as e:
            logger.error(f"Failed to start ZAP instance: {e}")
            return False

    def _start_docker_zap(self) -> bool:
        """Start ZAP in Docker container"""
        try:
            client = docker.from_env()

            # Check if container already exists
            container_name = f"zap-scanner-{int(time.time())}"

            logger.info(f"Starting ZAP Docker container: {container_name}")

            # Start ZAP container
            self.docker_container = client.containers.run(
                image=ZAPConfig.ZAP_DOCKER_IMAGE,
                name=container_name,
                detach=True,
                remove=True,
                ports={f"{self.zap_port}/tcp": self.zap_port},
                command=[
                    "zap.sh",
                    "-daemon",
                    "-host", "0.0.0.0",
                    "-port", str(self.zap_port),
                    "-config", f"api.key={self.zap_api_key}",
                    "-config", "api.addrs.addr.name=.*",
                    "-config", "api.addrs.addr.regex=true",
                ],
            )

            # Wait for ZAP to be ready
            max_wait = 60  # seconds
            wait_interval = 2
            elapsed = 0

            while elapsed < max_wait:
                try:
                    self.zap = ZAPv2(
                        apikey=self.zap_api_key,
                        proxies={
                            "http": f"http://{self.zap_host}:{self.zap_port}",
                            "https": f"http://{self.zap_host}:{self.zap_port}",
                        }
                    )
                    self.zap.core.version
                    logger.info(f"ZAP Docker container is ready: {container_name}")
                    return True
                except Exception:
                    time.sleep(wait_interval)
                    elapsed += wait_interval

            logger.error("ZAP container failed to start within timeout")
            self.stop_zap_instance()
            return False

        except Exception as e:
            logger.error(f"Failed to start ZAP Docker container: {e}")
            self.stop_zap_instance()
            return False

    def stop_zap_instance(self) -> None:
        """Stop ZAP instance"""
        try:
            if self.docker_container:
                logger.info("Stopping ZAP Docker container")
                self.docker_container.stop(timeout=10)
                self.docker_container = None
        except Exception as e:
            logger.error(f"Error stopping ZAP container: {e}")

    def spider_scan(
        self,
        target_url: str,
        max_depth: int = 5,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        Run spider scan to discover URLs
        Returns: scan_id
        """
        zap = self._ensure_zap_initialized()
        logger.info(f"Starting spider scan for {target_url}")

        # Start spider
        scan_id = zap.spider.scan(target_url, maxchildren=None, recurse=True)

        # Monitor progress
        while int(zap.spider.status(scan_id)) < 100:
            progress = int(zap.spider.status(scan_id))
            if progress_callback:
                progress_callback(progress, f"Spidering: {progress}%")
            time.sleep(2)

        logger.info(f"Spider scan completed for {target_url}")
        return scan_id

    def passive_scan(
        self,
        target_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> None:
        """Wait for passive scan to complete"""
        zap = self._ensure_zap_initialized()
        logger.info(f"Running passive scan for {target_url}")

        # Access the URL to trigger passive scan
        zap.core.access_url(target_url, followredirects=True)

        # Wait for passive scan to complete
        while int(zap.pscan.records_to_scan) > 0:
            remaining = int(zap.pscan.records_to_scan)
            if progress_callback:
                progress_callback(0, f"Passive scan: {remaining} records remaining")
            time.sleep(2)

        logger.info(f"Passive scan completed for {target_url}")

    def active_scan(
        self,
        target_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        Run active scan
        Returns: scan_id
        """
        zap = self._ensure_zap_initialized()
        logger.info(f"Starting active scan for {target_url}")

        # Start active scan
        scan_id = zap.ascan.scan(target_url)

        # Monitor progress
        while int(zap.ascan.status(scan_id)) < 100:
            progress = int(zap.ascan.status(scan_id))
            if progress_callback:
                progress_callback(progress, f"Active scanning: {progress}%")
            time.sleep(5)

        logger.info(f"Active scan completed for {target_url}")
        return scan_id

    def get_alerts(self, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all alerts from ZAP"""
        zap = self._ensure_zap_initialized()
        try:
            if base_url:
                alerts = zap.core.alerts(baseurl=base_url)
            else:
                alerts = zap.core.alerts()
            return alerts
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    def run_basic_scan(
        self,
        target_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Basic scan: Spider + Passive scan (No domain verification required)
        This is a non-intrusive scan that only observes and doesn't actively test the target
        """
        logger.info(f"Starting BASIC scan for {target_url}")
        if not self.start_zap_instance():
            raise Exception("Failed to start ZAP instance")

        try:
            # Spider - discover URLs
            if progress_callback:
                progress_callback(0, "Starting spider scan")
            self.spider_scan(target_url, progress_callback=progress_callback)

            # Passive scan - analyze discovered URLs
            if progress_callback:
                progress_callback(50, "Running passive scan")
            self.passive_scan(target_url, progress_callback=progress_callback)

            # Get results
            if progress_callback:
                progress_callback(100, "Collecting results")
            alerts = self.get_alerts(target_url)
            logger.info(f"BASIC scan completed for {target_url}. Found {len(alerts)} alerts")
            return alerts
        finally:
            self.stop_zap_instance()

    def run_full_scan(
        self,
        target_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Full scan: Spider + Passive + Active scan (Requires domain verification)
        This is an intrusive scan that actively tests the target for vulnerabilities
        """
        logger.info(f"Starting FULL scan for {target_url}")
        if not self.start_zap_instance():
            raise Exception("Failed to start ZAP instance")

        try:
            # Spider - discover URLs
            if progress_callback:
                progress_callback(0, "Starting spider scan")
            self.spider_scan(target_url, progress_callback=progress_callback)

            # Passive scan - analyze discovered URLs
            if progress_callback:
                progress_callback(33, "Running passive scan")
            self.passive_scan(target_url, progress_callback=progress_callback)

            # Active scan - actively test for vulnerabilities
            if progress_callback:
                progress_callback(66, "Starting active scan")
            self.active_scan(target_url, progress_callback=progress_callback)

            # Get results
            if progress_callback:
                progress_callback(100, "Collecting results")
            alerts = self.get_alerts(target_url)
            logger.info(f"FULL scan completed for {target_url}. Found {len(alerts)} alerts")
            return alerts
        finally:
            self.stop_zap_instance()
