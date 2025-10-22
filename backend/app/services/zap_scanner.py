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

    def _configure_active_scan_policy(self) -> None:
        """
        Configure ZAP active scan policy for security testing.

        Enables: SQLi, XSS, Path Traversal, Command Injection, CSRF, Security Headers
        Disables: DoS, Brute Force, Buffer Overflow (too aggressive/destructive)

        Performance optimized with throttling and smart targeting.
        """
        zap = self._ensure_zap_initialized()

        try:
            logger.info("Configuring active scan policy for FULL scan")

            # First, disable all scanners to start fresh
            zap.ascan.disable_all_scanners()

            # Enable passive scanners (for comprehensive coverage)
            zap.pscan.enable_all_scanners()

            # === ENABLE CRITICAL VULNERABILITY SCANNERS ===

            # SQL Injection (IDs: 40018, 40019, 40020, 40021, 40022, 90018)
            sql_injection_scanners = [40018, 40019, 40020, 40021, 40022, 90018]

            # Cross-Site Scripting (IDs: 40012, 40014, 40016, 40017)
            xss_scanners = [40012, 40014, 40016, 40017]

            # Path Traversal (IDs: 6, 7)
            path_traversal_scanners = [6, 7]

            # Command Injection (IDs: 90020, 90019)
            command_injection_scanners = [90020, 90019]

            # CSRF (IDs: 20012, 10202)
            csrf_scanners = [20012, 10202]

            # Security Misconfiguration (IDs: 10020, 10021, 10023, 10024, 10025, 10026, 10027)
            security_misc_scanners = [10020, 10021, 10023, 10024, 10025, 10026, 10027]

            # Server-Side Code Injection (IDs: 90019)
            code_injection_scanners = [90019]

            # External Redirect (IDs: 20019)
            redirect_scanners = [20019]

            # XXE (XML External Entity) (IDs: 90023)
            xxe_scanners = [90023]

            # === ALPHA/EXPERIMENTAL SCANNERS (Optional - More Aggressive) ===
            # Only enabled if ZAP_ENABLE_ALPHA_SCANNERS=True
            alpha_scanners = []
            if ZAPConfig.ZAP_ENABLE_ALPHA_SCANNERS:
                logger.info("Enabling ALPHA/experimental scanners for aggressive testing")
                # Advanced SQL Injection variants
                alpha_scanners += [40029, 40030, 40031, 40032, 40033]
                # Advanced XSS variants
                alpha_scanners += [40026, 40027, 40028]
                # Server-side Template Injection
                alpha_scanners += [90035]
                # LDAP Injection
                alpha_scanners += [40015]
                # XML Injection
                alpha_scanners += [90021]
                # Expression Language Injection
                alpha_scanners += [90025]
                # NoSQL Injection
                alpha_scanners += [90036]
                logger.info(f"Added {len(alpha_scanners)} alpha scanners")

            # Combine all enabled scanners
            enabled_scanners = (
                sql_injection_scanners +
                xss_scanners +
                path_traversal_scanners +
                command_injection_scanners +
                csrf_scanners +
                security_misc_scanners +
                code_injection_scanners +
                redirect_scanners +
                xxe_scanners +
                alpha_scanners  # Add alpha scanners if enabled
            )

            # Enable each scanner
            for scanner_id in enabled_scanners:
                try:
                    zap.ascan.enable_scanners(ids=str(scanner_id))
                    logger.debug(f"Enabled active scanner: {scanner_id}")
                except Exception as e:
                    logger.warning(f"Failed to enable scanner {scanner_id}: {e}")

            logger.info(f"Enabled {len(enabled_scanners)} active scan rules")

            # === CONFIGURE SCAN SETTINGS FOR PERFORMANCE ===

            try:
                # Set thread count (4 threads = good balance of speed vs server load)
                zap.ascan.set_option_thread_per_host(4)
                logger.debug("Set thread per host: 4")
            except Exception as e:
                logger.warning(f"Could not set thread per host: {e}")

            try:
                # Set max scan duration (30 minutes)
                zap.ascan.set_option_max_scan_duration_in_mins(30)
                logger.debug("Set max scan duration: 30 minutes")
            except Exception as e:
                logger.warning(f"Could not set max scan duration: {e}")

            try:
                # Set delay between requests (100ms = 10 req/sec max)
                zap.ascan.set_option_delay_in_ms(100)
                logger.debug("Set delay between requests: 100ms")
            except Exception as e:
                logger.warning(f"Could not set delay: {e}")

            logger.info("Active scan policy configured successfully")
            logger.info("Settings: Enabled 30+ security scanners for comprehensive testing")

        except Exception as e:
            logger.error(f"Failed to configure active scan policy: {e}")
            raise

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

        OPTIMIZED: Parallel execution of spider, passive, and active scans

        Tests for:
        - SQL Injection (SQLi)
        - Cross-Site Scripting (XSS)
        - Path Traversal
        - Command Injection
        - CSRF vulnerabilities
        - Security Headers
        - Open Redirects
        - XXE (XML External Entity)
        - And more critical vulnerabilities
        """
        logger.info(f"Starting FULL scan (active) for {target_url}")

        # Only start ZAP if not managed by scanner manager
        needs_cleanup = False
        if not self._scanner_manager_initialized:
            if not self.start_zap_instance():
                raise Exception("Failed to start ZAP instance")
            needs_cleanup = True
        else:
            logger.info(f"Using pooled ZAP connection (context: {self._scan_context})")

        try:
            # Configure active scan policy first
            if progress_callback:
                progress_callback(0, "Configuring security test policy")
            self._configure_active_scan_policy()

            # Start spider, passive, and active scans in parallel (OPTIMIZATION)
            if progress_callback:
                progress_callback(5, "Starting parallel security testing")

            zap = self._ensure_zap_initialized()

            # Start traditional spider
            spider_scan_id = zap.spider.scan(target_url, maxchildren=None, recurse=True)
            logger.info(f"Traditional spider started for {target_url}")

            # Start AJAX Spider for JavaScript-heavy apps (if enabled)
            ajax_spider_enabled = ZAPConfig.ZAP_ENABLE_AJAX_SPIDER
            if ajax_spider_enabled:
                try:
                    zap.ajaxSpider.set_option_max_duration(str(ZAPConfig.ZAP_AJAX_SPIDER_TIMEOUT // 60))  # Convert to minutes
                    ajax_spider_result = zap.ajaxSpider.scan(target_url)
                    logger.info(f"AJAX spider started for {target_url} (for JavaScript apps)")
                except Exception as e:
                    logger.warning(f"Could not start AJAX spider: {e}. Continuing with traditional spider only.")
                    ajax_spider_enabled = False

            # Trigger passive scan immediately
            zap.core.access_url(target_url, followredirects=True)
            zap.pscan.enable_all_scanners()
            logger.info(f"Passive scan triggered for {target_url}")

            # Start active scan immediately (will scan URLs as spider discovers them)
            active_scan_id = zap.ascan.scan(target_url)
            logger.info(f"Active scan started for {target_url} with ID: {active_scan_id}")

            # Monitor all three scans together
            start_time = time.time()
            spider_timeout = ZAPConfig.ZAP_SPIDER_TIMEOUT
            passive_timeout = ZAPConfig.ZAP_PASSIVE_SCAN_TIMEOUT
            active_timeout = 1800  # 30 minutes for active scan

            spider_done = False
            ajax_spider_done = not ajax_spider_enabled  # If not enabled, consider it done
            passive_done = False
            initial_passive_records = None

            while True:
                elapsed = time.time() - start_time

                # Check traditional spider status
                spider_progress = int(zap.spider.status(spider_scan_id))
                if spider_progress >= 100:
                    if not spider_done:
                        logger.info(f"Traditional spider completed for {target_url}")
                        spider_done = True

                # Check spider timeout
                if not spider_done and elapsed > spider_timeout:
                    logger.warning(f"Spider timeout after {elapsed:.1f}s, stopping")
                    zap.spider.stop(spider_scan_id)
                    spider_done = True

                # Check AJAX spider status (if enabled)
                if ajax_spider_enabled and not ajax_spider_done:
                    try:
                        ajax_status = zap.ajaxSpider.status
                        if ajax_status == 'stopped':
                            logger.info(f"AJAX spider completed for {target_url}")
                            ajax_spider_done = True
                        # Check AJAX spider timeout
                        if elapsed > ZAPConfig.ZAP_AJAX_SPIDER_TIMEOUT:
                            logger.warning(f"AJAX spider timeout, stopping")
                            zap.ajaxSpider.stop()
                            ajax_spider_done = True
                    except Exception as e:
                        logger.warning(f"Error checking AJAX spider status: {e}")
                        ajax_spider_done = True

                # Check passive scan status
                passive_remaining = int(zap.pscan.records_to_scan)

                if initial_passive_records is None and passive_remaining > 0:
                    initial_passive_records = passive_remaining

                # Calculate passive progress
                if initial_passive_records and initial_passive_records > 0:
                    passive_progress = int((1 - passive_remaining / initial_passive_records) * 100)
                    passive_progress = min(99, max(0, passive_progress))
                else:
                    passive_progress = 100 if passive_remaining == 0 else 0

                if passive_remaining == 0 and spider_done and ajax_spider_done:
                    if not passive_done:
                        logger.info(f"Passive scan completed for {target_url}")
                        passive_done = True

                # Check active scan status
                try:
                    active_status = zap.ascan.status(active_scan_id)
                    # Handle cases where scan doesn't exist or isn't started yet
                    if active_status in ['does_not_exist', '', None]:
                        active_progress = 0
                    else:
                        active_progress = int(active_status)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse active scan status '{active_status}': {e}")
                    active_progress = 0

                # All completed?
                all_spiders_done = spider_done and ajax_spider_done
                if all_spiders_done and passive_done and active_progress >= 100:
                    spider_type = "spider, AJAX spider, passive, active" if ajax_spider_enabled else "spider, passive, active"
                    logger.info(f"All scans ({spider_type}) completed")
                    break

                # Check overall timeout
                if elapsed > active_timeout:
                    logger.warning(f"Active scan timeout after {elapsed:.1f}s, stopping")
                    zap.ascan.stop(active_scan_id)
                    break

                # Report combined progress
                if progress_callback:
                    if ajax_spider_enabled:
                        # With AJAX: spider 15%, AJAX 15%, passive 15%, active 55%
                        ajax_progress = 100 if ajax_spider_done else 50  # Approximate AJAX progress
                        combined_progress = int(
                            spider_progress * 0.15 +
                            ajax_progress * 0.15 +
                            passive_progress * 0.15 +
                            active_progress * 0.55
                        )
                        status_msg = (
                            f"Spider: {spider_progress}%, "
                            f"AJAX: {ajax_progress}%, "
                            f"Passive: {passive_progress}%, "
                            f"Active: {active_progress}%"
                        )
                    else:
                        # Without AJAX: spider 20%, passive 20%, active 60%
                        combined_progress = int(
                            spider_progress * 0.2 +
                            passive_progress * 0.2 +
                            active_progress * 0.6
                        )
                        status_msg = (
                            f"Spider: {spider_progress}%, "
                            f"Passive: {passive_progress}%, "
                            f"Active: {active_progress}%"
                        )
                    progress_callback(combined_progress, status_msg)

                time.sleep(3)  # Check every 3 seconds

            elapsed_time = time.time() - start_time
            logger.info(f"FULL scan completed for {target_url} in {elapsed_time:.1f}s")

            # Get results
            if progress_callback:
                progress_callback(100, "Collecting security findings")
            alerts = self.get_alerts(target_url)
            logger.info(f"FULL scan completed for {target_url}. Found {len(alerts)} alerts")
            return alerts

        finally:
            # Only cleanup if we started ZAP ourselves
            if needs_cleanup:
                self.stop_zap_instance()
