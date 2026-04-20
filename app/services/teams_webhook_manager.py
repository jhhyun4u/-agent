"""
Teams Webhook Manager - URL validation, health checks, retry logic
Phase 2 DO Phase: Day 3-4 Implementation
Design Ref: §3.5, Vault Chat Phase 2 Technical Design
"""

import aiohttp
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebhookHealth:
    """Webhook health status"""
    url: str
    is_healthy: bool
    last_check: datetime
    last_error: Optional[str]
    consecutive_failures: int


class TeamsWebhookManager:
    """
    Manage Teams Webhook URLs - Validation, health checks, delivery

    Responsibilities:
    1. Validate webhook URL format and liveness
    2. Send messages with retry logic
    3. Monitor webhook health
    4. Handle rate limiting and errors
    """

    # Teams webhook URL pattern (strict validation)
    TEAMS_WEBHOOK_PATTERN = re.compile(
        r"^https://outlook\.webhook\.office\.com/webhookb2?/[a-z0-9\-]+@[a-z0-9\-]+/[a-z0-9\-]+/[a-zA-Z0-9\-]+$",
        re.IGNORECASE
    )

    # Health check configuration
    HEALTH_CHECK_TIMEOUT = 5  # seconds
    MAX_CONSECUTIVE_FAILURES = 3
    HEALTH_CHECK_INTERVAL = 3600  # 1 hour

    # Retry configuration
    DEFAULT_RETRIES = 3
    RETRY_BACKOFF_MULTIPLIER = 2  # exponential: 1s, 2s, 4s
    RATE_LIMIT_RETRY_MULTIPLIER = 5  # longer wait for 429

    def __init__(self):
        """Initialize Teams Webhook Manager"""
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.health_cache: Dict[str, WebhookHealth] = {}

    async def initialize(self) -> None:
        """Initialize HTTP session at startup"""
        if not self.http_session:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            logger.info("Teams Webhook Manager initialized")

    async def close(self) -> None:
        """Clean up HTTP session at shutdown"""
        if self.http_session:
            await self.http_session.close()
            logger.info("Teams Webhook Manager closed")

    # ── URL Validation ──

    async def validate_webhook_url(self, webhook_url: str) -> bool:
        """
        Validate Teams webhook URL format and liveness

        Checks:
        1. HTTPS protocol (required for security)
        2. outlook.webhook.office.com domain
        3. Valid URL format (regex)
        4. Webhook is live (HEAD request)

        Args:
            webhook_url: URL to validate

        Returns:
            bool: True if valid and live
        """
        # Check 1: Basic format validation
        if not self._is_valid_format(webhook_url):
            logger.error(f"Invalid webhook URL format: {webhook_url[:50]}...")
            return False

        # Check 2: HTTPS requirement
        if not webhook_url.startswith("https://"):
            logger.error("Webhook URL must use HTTPS protocol")
            return False

        # Check 3: Domain validation
        if "outlook.webhook.office.com" not in webhook_url:
            logger.error("Webhook URL must be from outlook.webhook.office.com domain")
            return False

        # Check 4: Liveness check (HEAD request)
        is_live = await self._check_webhook_liveness(webhook_url)
        if not is_live:
            logger.warning(f"Webhook URL is not responding: {webhook_url[:50]}...")
            return False

        logger.info(f"Webhook URL validated: {webhook_url[:50]}...")
        return True

    def _is_valid_format(self, webhook_url: str) -> bool:
        """
        Check webhook URL format against Teams pattern

        Args:
            webhook_url: URL to check

        Returns:
            bool: True if format is valid
        """
        if not webhook_url or not isinstance(webhook_url, str):
            return False

        # Pattern match: https://outlook.webhook.office.com/webhookb2/...
        if not self.TEAMS_WEBHOOK_PATTERN.match(webhook_url):
            logger.debug(f"URL does not match Teams webhook pattern: {webhook_url[:50]}...")
            return False

        return True

    async def _check_webhook_liveness(self, webhook_url: str) -> bool:
        """
        Check if webhook is responding (HEAD request)

        Args:
            webhook_url: Webhook URL to check

        Returns:
            bool: True if webhook is live
        """
        if not self.http_session:
            await self.initialize()

        try:
            async with self.http_session.head(
                webhook_url,
                timeout=aiohttp.ClientTimeout(total=self.HEALTH_CHECK_TIMEOUT)
            ) as resp:
                # Teams webhook returns 200/204 for HEAD request
                is_live = resp.status in (200, 204)
                logger.debug(f"Webhook liveness check: {resp.status} ({'live' if is_live else 'dead'})")
                return is_live

        except asyncio.TimeoutError:
            logger.warning(f"Webhook liveness check timeout: {webhook_url[:50]}...")
            return False

        except aiohttp.ClientError as e:
            logger.warning(f"Webhook liveness check failed: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error in liveness check: {e}")
            return False

    # ── Message Sending ──

    async def send_message(
        self,
        webhook_url: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send message via Teams webhook (single attempt, no retry)

        Args:
            webhook_url: Webhook URL
            message: Message payload (Adaptive Card JSON)

        Returns:
            bool: Success of send
        """
        if not self.http_session:
            await self.initialize()

        try:
            async with self.http_session.post(
                webhook_url,
                json=message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.debug(f"Message sent successfully to {webhook_url[:50]}...")
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Webhook error {resp.status}: {text[:200]}")
                    return False

        except Exception as e:
            logger.error(f"Message send failed: {e}")
            return False

    async def send_message_with_retry(
        self,
        webhook_url: str,
        message: Dict[str, Any],
        max_retries: int = DEFAULT_RETRIES
    ) -> bool:
        """
        Send message via Teams webhook with exponential backoff retry

        Retry strategy:
        - Exponential backoff: 1s, 2s, 4s
        - Retry on: connection errors, 5xx, timeout, 429
        - No retry on: 4xx (except 429)

        Args:
            webhook_url: Webhook URL
            message: Message payload
            max_retries: Maximum retry attempts (default 3)

        Returns:
            bool: Success of send
        """
        if not self.http_session:
            await self.initialize()

        last_error = None
        last_status = None

        for attempt in range(max_retries):
            try:
                async with self.http_session.post(
                    webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    last_status = resp.status

                    if resp.status == 200:
                        logger.info(f"Message sent successfully (attempt {attempt + 1}/{max_retries})")
                        self._update_health(webhook_url, is_healthy=True)
                        return True

                    elif resp.status == 429:  # Rate limit
                        # Use longer wait for rate limiting
                        wait_time = self.RATE_LIMIT_RETRY_MULTIPLIER ** attempt
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry...")
                            import asyncio
                            await asyncio.sleep(wait_time)
                        continue

                    elif 500 <= resp.status < 600:  # Server error (retryable)
                        text = await resp.text()
                        last_error = f"Server error {resp.status}: {text[:100]}"
                        if attempt < max_retries - 1:
                            wait_time = self.RETRY_BACKOFF_MULTIPLIER ** attempt
                            logger.warning(f"Server error {resp.status}. Retrying in {wait_time}s...")
                            import asyncio
                            await asyncio.sleep(wait_time)
                        continue

                    else:  # 4xx (not retryable except 429)
                        text = await resp.text()
                        last_error = f"Client error {resp.status}: {text[:100]}"
                        logger.error(f"Webhook client error {resp.status}: {text[:200]}")
                        self._update_health(webhook_url, is_healthy=False, error=last_error)
                        return False

            except (aiohttp.ClientError, Exception) as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait_time = self.RETRY_BACKOFF_MULTIPLIER ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    import asyncio
                    await asyncio.sleep(wait_time)
                continue

        # All retries exhausted
        self._update_health(webhook_url, is_healthy=False, error=last_error)
        logger.error(
            f"Message delivery failed after {max_retries} attempts. "
            f"Last error: {last_error} (status: {last_status})"
        )
        return False

    # ── Health Management ──

    async def health_check_all(self, urls: List[str]) -> Dict[str, bool]:
        """
        Check health of multiple webhook URLs

        Args:
            urls: List of webhook URLs to check

        Returns:
            Dict mapping URL to health status (True/False)
        """
        if not self.http_session:
            await self.initialize()

        results = {}

        for url in urls:
            # Check cache first
            cached_health = self.health_cache.get(url)
            if cached_health:
                # Use cache if recent (within interval)
                age = datetime.utcnow() - cached_health.last_check
                if age.total_seconds() < self.HEALTH_CHECK_INTERVAL:
                    results[url] = cached_health.is_healthy
                    continue

            # Perform fresh health check
            is_healthy = await self._check_webhook_liveness(url)
            self._update_health(url, is_healthy=is_healthy)
            results[url] = is_healthy

        logger.info(f"Health check results: {sum(results.values())}/{len(results)} healthy")
        return results

    def _update_health(
        self,
        webhook_url: str,
        is_healthy: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Update webhook health status in cache

        Args:
            webhook_url: Webhook URL
            is_healthy: Current health status
            error: Error message (if unhealthy)
        """
        existing = self.health_cache.get(webhook_url)

        if is_healthy:
            # Reset failure count on success
            consecutive_failures = 0
        else:
            # Increment failure count on failure
            consecutive_failures = (existing.consecutive_failures if existing else 0) + 1

        self.health_cache[webhook_url] = WebhookHealth(
            url=webhook_url,
            is_healthy=is_healthy,
            last_check=datetime.utcnow(),
            last_error=error,
            consecutive_failures=consecutive_failures
        )

        # Log if exceeded failure threshold
        if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            logger.error(
                f"Webhook unhealthy (failures: {consecutive_failures}): {webhook_url[:50]}... "
                f"({error})"
            )

    def get_health(self, webhook_url: str) -> Optional[WebhookHealth]:
        """
        Get cached health status for webhook

        Args:
            webhook_url: Webhook URL

        Returns:
            WebhookHealth or None if not checked yet
        """
        return self.health_cache.get(webhook_url)

    # ── Error Handling ──

    @staticmethod
    def format_error_message(status_code: int, text: str) -> str:
        """
        Format webhook error for logging

        Args:
            status_code: HTTP status code
            text: Response text

        Returns:
            Formatted error message
        """
        if status_code == 429:
            return "Rate limited by Teams API"
        elif status_code == 404:
            return "Webhook URL not found (may be invalid or expired)"
        elif status_code == 401:
            return "Webhook authentication failed"
        elif 500 <= status_code < 600:
            return f"Teams service error ({status_code})"
        else:
            return f"Webhook error: {text[:100]}"


# Async import at module level for retry logic
import asyncio
