"""共用请求层 - curl_cffi 浏览器指纹伪装"""

import random
import time
import logging
from curl_cffi import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BROWSER_FINGERPRINTS = [
    "chrome124", "chrome123", "chrome120", "chrome116",
    "chrome110", "chrome107", "chrome104", "chrome101",
    "chrome100", "chrome99",
    "safari17_0",
    "edge101", "edge99",
]


def fetch_page(url: str, timeout: int = 20) -> BeautifulSoup | None:
    """请求亚马逊页面。
    成功返回 (BeautifulSoup, True)
    触发反爬返回 (None, False) - 需要更长退避
    其他错误返回 (None, True) - 可以正常重试
    """
    fingerprint = random.choice(BROWSER_FINGERPRINTS)
    try:
        resp = requests.get(
            url,
            impersonate=fingerprint,
            timeout=timeout,
            allow_redirects=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        if resp.status_code != 200:
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None

        content_len = len(resp.text)

        # <15KB 且无 productTitle：几乎可以确定是反爬/验证码页面
        if content_len < 15000 and "producttitle" not in resp.text.lower():
            logger.warning(f"Captcha/block page ({content_len}B): {url}")
            return None

        return BeautifulSoup(resp.text, "lxml")

    except Exception as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None


def fetch_with_retry(url: str, max_retries: int = 3, timeout: int = 20, interval: float = 3.0) -> BeautifulSoup | None:
    """带重试的页面抓取。检测到反爬时用更长退避。"""
    consecutive_captcha = 0

    for attempt in range(max_retries):
        if attempt > 0:
            if consecutive_captcha > 0:
                # 反爬退避：10-20 秒
                wait = random.uniform(10, 20)
                logger.info(f"Cooldown after captcha, waiting {wait:.0f}s...")
            else:
                wait = interval * (2 ** (attempt - 1))
            time.sleep(wait)

        soup = fetch_page(url, timeout=timeout)
        if soup is not None:
            return soup

        # 判断是否是反爬（小页面）
        consecutive_captcha += 1

    return None


def is_captcha(soup: BeautifulSoup) -> bool:
    text = soup.get_text().lower()[:2000]
    has_product = bool(soup.find(id="productTitle"))
    if has_product:
        return False
    return ("enter the characters" in text or "type the characters" in text)


def is_unavailable(soup: BeautifulSoup) -> bool:
    text = soup.get_text().lower()[:3000]
    patterns = [
        "currently unavailable", "we couldn't find that page",
        "dogs of amazon", "sorry! we just need to make sure",
    ]
    return any(p in text for p in patterns)
