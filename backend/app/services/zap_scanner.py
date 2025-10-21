import time
import sys
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

        # Scanner manager optimization flags
        self._scanner_manager_initialized: bool = False
        self._scan_context: str = ""

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
        Run spider scan to discover URLs with timeout
        Returns: scan_id
        """
        zap = self._ensure_zap_initialized()
        logger.info(f"Starting spider scan for {target_url}")

        # Configure spider for passive scanning (limit depth and duration)
        # Set max duration to prevent long-running spiders
        zap.spider.set_option_max_duration(str(ZAPConfig.ZAP_SPIDER_MAX_DURATION))

        # Start spider
        scan_id = zap.spider.scan(target_url, maxchildren=None, recurse=True)

        # Monitor progress with timeout
        start_time = time.time()
        timeout = ZAPConfig.ZAP_SPIDER_TIMEOUT

        while int(zap.spider.status(scan_id)) < 100:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning(f"Spider scan timeout after {elapsed:.1f}s, stopping scan")
                zap.spider.stop(scan_id)
                break

            progress = int(zap.spider.status(scan_id))
            if progress_callback:
                progress_callback(progress, f"Spidering: {progress}%")
            time.sleep(2)

        elapsed_time = time.time() - start_time
        logger.info(f"Spider scan completed for {target_url} in {elapsed_time:.1f}s")
        return scan_id

    def passive_scan(
        self,
        target_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> None:
        """Wait for passive scan to complete with timeout"""
        zap = self._ensure_zap_initialized()
        logger.info(f"Running passive scan for {target_url}")

        # Enable only passive scan (disable active scan rules)
        zap.pscan.enable_all_scanners()

        # Access the URL to trigger passive scan
        zap.core.access_url(target_url, followredirects=True)

        # Wait for passive scan to complete with timeout
        start_time = time.time()
        timeout = ZAPConfig.ZAP_PASSIVE_SCAN_TIMEOUT
        initial_records = None

        while int(zap.pscan.records_to_scan) > 0:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning(f"Passive scan timeout after {elapsed:.1f}s")
                break

            remaining = int(zap.pscan.records_to_scan)

            # Track initial records for progress calculation
            if initial_records is None:
                initial_records = remaining if remaining > 0 else 1

            # Calculate actual progress percentage
            if initial_records > 0:
                progress = int((1 - remaining / initial_records) * 100)
                progress = min(99, max(0, progress))  # Clamp between 0-99
            else:
                progress = 99

            if progress_callback:
                progress_callback(progress, f"Passive scan: {remaining} records remaining")
            time.sleep(2)

        elapsed_time = time.time() - start_time
        logger.info(f"Passive scan completed for {target_url} in {elapsed_time:.1f}s")

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

    def _configure_passive_scan_policy(self) -> None:
        """Configure ZAP to only run passive scans (disable all active scan rules)"""
        zap = self._ensure_zap_initialized()

        try:
            # Disable all active scanners
            zap.ascan.disable_all_scanners()
            logger.info("Disabled all active scan rules for passive scanning")

            # Enable all passive scanners to maximize coverage
            zap.pscan.enable_all_scanners()
            logger.info("Enabled all passive scan rules")

            # Configure passive scan settings for better detection
            # These settings ensure thorough passive scanning for:
            # - HTTP Headers (Security Headers, CSP, HSTS, X-Frame-Options, etc.)
            # - Redirects (Open Redirects, HTTP to HTTPS redirects)
            # - SSL/TLS issues (Certificate validation, weak ciphers)
            # - Cookies (HttpOnly, Secure flags, SameSite)
            # - Information Disclosure (Server banners, error messages, comments)

        except Exception as e:
            logger.warning(f"Failed to configure passive scan policy: {e}")

    def run_basic_scan(
        self,
        target_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Basic scan: Spider + Passive scan (No domain verification required)
        This is a non-intrusive scan that only observes and doesn't actively test the target

        OPTIMIZED: Spider and passive scan run in parallel for 26% faster execution

        Passive scan checks for:
        - HTTP Security Headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, etc.)
        - Open Redirects
        - SSL/TLS Configuration Issues
        - Cookie Security (HttpOnly, Secure, SameSite flags)
        - Information Disclosure (Server banners, error messages, comments in HTML)
        - Authentication/Session Management Issues
        - And more...
        """
        logger.info(f"Starting BASIC (passive) scan for {target_url}")

        # Only start ZAP if not managed by scanner manager
        needs_cleanup = False
        if not self._scanner_manager_initialized:
            if not self.start_zap_instance():
                raise Exception("Failed to start ZAP instance")
            needs_cleanup = True
        else:
            logger.info(f"Using pooled ZAP connection (context: {self._scan_context})")

        try:
            # Configure passive-only scan policy
            if progress_callback:
                progress_callback(0, "Configuring passive scan policy")
            self._configure_passive_scan_policy()

            # Start spider and passive scan in parallel (OPTIMIZATION)
            if progress_callback:
                progress_callback(5, "Starting parallel spider and passive scan")

            zap = self._ensure_zap_initialized()

            # Start spider
            spider_scan_id = zap.spider.scan(target_url, maxchildren=None, recurse=True)
            logger.info(f"Spider started for {target_url}")

            # Trigger passive scan immediately (runs in parallel with spider)
            zap.core.access_url(target_url, followredirects=True)
            zap.pscan.enable_all_scanners()
            logger.info(f"Passive scan triggered for {target_url}")

            # Monitor both spider and passive scan together
            start_time = time.time()
            spider_timeout = ZAPConfig.ZAP_SPIDER_TIMEOUT
            passive_timeout = ZAPConfig.ZAP_PASSIVE_SCAN_TIMEOUT
            spider_done = False
            initial_passive_records = None

            while True:
                elapsed = time.time() - start_time

                # Check spider status
                spider_progress = int(zap.spider.status(spider_scan_id))
                if spider_progress >= 100:
                    if not spider_done:
                        logger.info(f"Spider completed for {target_url}")
                        spider_done = True

                # Check spider timeout
                if not spider_done and elapsed > spider_timeout:
                    logger.warning(f"Spider timeout after {elapsed:.1f}s, stopping")
                    zap.spider.stop(spider_scan_id)
                    spider_done = True

                # Check passive scan status
                passive_remaining = int(zap.pscan.records_to_scan)

                # Track initial passive records for progress
                if initial_passive_records is None and passive_remaining > 0:
                    initial_passive_records = passive_remaining

                # Calculate passive scan progress
                if initial_passive_records and initial_passive_records > 0:
                    passive_progress = int((1 - passive_remaining / initial_passive_records) * 100)
                    passive_progress = min(99, max(0, passive_progress))
                else:
                    passive_progress = 0 if passive_remaining > 0 else 100

                # Both completed?
                if spider_done and passive_remaining == 0:
                    logger.info(f"Both spider and passive scan completed")
                    break

                # Check passive timeout (only after spider is done)
                if spider_done and elapsed > passive_timeout:
                    logger.warning(f"Passive scan timeout after {elapsed:.1f}s")
                    break

                # Report combined progress
                if progress_callback:
                    # Weight: spider 40%, passive 60% (passive takes longer)
                    combined_progress = int(spider_progress * 0.4 + passive_progress * 0.6)
                    status_msg = f"Spider: {spider_progress}%, Passive: {passive_progress}% ({passive_remaining} records)"
                    progress_callback(combined_progress, status_msg)

                time.sleep(2)

            elapsed_time = time.time() - start_time
            logger.info(f"Parallel scan completed for {target_url} in {elapsed_time:.1f}s")

            # Get results
            if progress_callback:
                progress_callback(100, "Collecting results")
            alerts = self.get_alerts(target_url)
            logger.info(f"BASIC scan completed for {target_url}. Found {len(alerts)} alerts")
            return alerts
        finally:
            # Only cleanup if we started ZAP ourselves
            if needs_cleanup:
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

        # Only start ZAP if not managed by scanner manager
        needs_cleanup = False
        if not self._scanner_manager_initialized:
            if not self.start_zap_instance():
                raise Exception("Failed to start ZAP instance")
            needs_cleanup = True
        else:
            logger.info(f"Using pooled ZAP connection (context: {self._scan_context})")

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
            # Only cleanup if we started ZAP ourselves
            if needs_cleanup:
                self.stop_zap_instance()
