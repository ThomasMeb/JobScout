"""Shared Playwright browser for JS-rendered scraping.

Usage:
    async with get_page() as page:
        await page.goto("https://example.com")
        html = await page.content()
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

_browser = None
_lock = asyncio.Lock()


async def _ensure_browser():
    """Launch a single Chromium instance (reused across scrapers)."""
    global _browser
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True)
        logger.info("Playwright browser launched")
    return _browser


class get_page:
    """Async context manager that provides a fresh browser page.

    - Blocks images, fonts, and media for performance
    - 30s default navigation timeout
    - Page is closed on exit
    """

    def __init__(self, timeout_ms: int = 30_000):
        self.timeout_ms = timeout_ms
        self.page = None

    async def __aenter__(self):
        async with _lock:
            browser = await _ensure_browser()
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )
        self.page = await ctx.new_page()
        self.page.set_default_navigation_timeout(self.timeout_ms)
        self.page.set_default_timeout(self.timeout_ms)

        # Block heavy resources for speed
        await self.page.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,eot,mp4,mp3}",
            lambda route: route.abort(),
        )
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            try:
                ctx = self.page.context
                await self.page.close()
                await ctx.close()
            except Exception:
                pass


async def close_browser():
    """Shutdown the shared browser (call at worker exit)."""
    global _browser
    if _browser and _browser.is_connected():
        await _browser.close()
        _browser = None
        logger.info("Playwright browser closed")
