import asyncio
import httpx
import random
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("app.scrapers.utils")

# Premium fallback User-Agents in case fake-useragent library fails or times out
FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

def get_random_user_agent() -> str:
    """Returns a randomized user agent, leveraging fake-useragent or our high-quality fallbacks."""
    try:
        from fake_useragent import UserAgent
        ua = UserAgent()
        return ua.random
    except Exception:
        return random.choice(FALLBACK_USER_AGENTS)

async def random_anti_block_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Executes a polite, asynchronous randomized delay to prevent rate limit blocks."""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)

def clean_html_content(raw_html: str) -> str:
    """Cleans a raw HTML string using BeautifulSoup, returning stripped plain text."""
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        # Remove script and style tags
        for element in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
            element.decompose()
        return soup.get_text(separator=" ").strip()
    except Exception as e:
        logger.error(f"HTML cleaning failed: {e}")
        return raw_html

async def verify_link(url: str) -> bool:
    """Pings a URL asynchronously to verify if it is valid (status < 400)."""
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        headers = {"User-Agent": get_random_user_agent()}
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(url, headers=headers, follow_redirects=True)
            if response.status_code < 400:
                return True
            # Fallback to GET in case HEAD is not allowed
            response = await client.get(url, headers=headers, follow_redirects=True)
            return response.status_code < 400
    except Exception:
        return False
