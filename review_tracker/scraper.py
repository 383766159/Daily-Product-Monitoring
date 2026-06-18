"""亚马逊产品页面抓取模块 - 使用 curl_cffi 实现浏览器指纹伪装"""
import re
import time
import random
import logging
from urllib.parse import urlparse

from curl_cffi import requests  # 替代标准 requests，支持 TLS 指纹伪装
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# curl_cffi 支持的浏览器指纹列表
BROWSER_FINGERPRINTS = [
    "chrome124", "chrome123", "chrome120", "chrome116",
    "chrome110", "chrome107", "chrome104", "chrome101",
    "chrome100", "chrome99",
    "firefox124", "firefox120",
    "safari17_0",
    "edge101", "edge99",
]

# 提取 ASIN 的正则
ASIN_PATTERN = re.compile(r"/dp/([A-Z0-9]{10})")
RATING_PATTERN = re.compile(r"([\d.]+)\s*out of")
NUMERIC_PATTERN = re.compile(r"[\d,.]+")


def extract_asin(url: str) -> str:
    """从亚马逊链接中提取 ASIN 码"""
    match = ASIN_PATTERN.search(url)
    if match:
        return match.group(1)
    if re.match(r"^[A-Z0-9]{10}$", url.strip()):
        return url.strip()
    raise ValueError(f"无法从链接中提取 ASIN: {url}")


def _parse_rating(soup: BeautifulSoup) -> float | None:
    """从页面试图解析星级评分"""
    selectors = [
        ("span", {"data-hook": "rating-out-of-text"}),
        ("span", {"class": "a-icon-alt"}),
        ("i", {"data-hook": "average-star-rating"}),
        ("div", {"id": "averageCustomerReviews_feature_div"}),
    ]

    for tag_name, attrs in selectors:
        elem = soup.find(tag_name, attrs)
        if elem:
            text = elem.get_text(strip=True)
            match = RATING_PATTERN.search(text)
            if match:
                return float(match.group(1))
            nums = NUMERIC_PATTERN.findall(text)
            for num in nums:
                try:
                    val = float(num.replace(",", ""))
                    if 1.0 <= val <= 5.0:
                        return val
                except ValueError:
                    continue

    return None


def _parse_review_count(soup: BeautifulSoup, page_text: str) -> int | None:
    """从页面解析评论/评分总数"""
    # 策略1: acrCustomerReviewText - 通常是最准确的
    elem = soup.find("span", id="acrCustomerReviewText")
    if elem:
        text = elem.get_text(strip=True)
        # 处理 "(31)" 或 "31 ratings" 格式
        nums = NUMERIC_PATTERN.findall(text)
        if nums:
            return int(nums[0].replace(",", ""))

    # 策略2: total-review-count
    elem = soup.find("span", {"data-hook": "total-review-count"})
    if elem:
        text = elem.get_text(strip=True)
        nums = NUMERIC_PATTERN.findall(text)
        if nums:
            return int(nums[0].replace(",", ""))

    # 策略3: 从页面文本中搜索 "global ratings" 模式
    import re as re_mod
    # 匹配 "4,561 global ratings" 或 "1,234 ratings"
    patterns = [
        r'([\d,]+)\s+global\s+ratings',
        r'([\d,]+)\s+ratings',
        r'"totalReviewCount":\s*(\d+)',
    ]
    for pat in patterns:
        match = re_mod.search(pat, page_text[:100000])
        if match:
            return int(match.group(1).replace(",", ""))

    return None


def _parse_title(soup: BeautifulSoup) -> str:
    """从页面解析产品标题"""
    elem = soup.find("span", id="productTitle")
    if elem:
        return elem.get_text(strip=True)
    return "未知产品"


def fetch_product(url: str, timeout: int = 15) -> dict:
    """抓取单个产品的评论数据（使用 curl_cffi 绕过反爬）

    返回:
        {
            "asin": str,
            "url": str,
            "title": str,
            "rating": float | None,
            "review_count": int | None,
            "error": str | None
        }
    """
    asin = extract_asin(url)
    result = {"asin": asin, "url": url, "title": "", "rating": None, "review_count": None, "error": None}

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
                "Cache-Control": "no-cache",
            },
        )

        if resp.status_code == 404:
            result["error"] = "产品页面不存在 (404)"
            return result

        if resp.status_code == 503:
            result["error"] = "亚马逊拒绝请求 (503)"
            return result

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            return result

        # 检测验证码页面
        page_text = resp.text
        if "captcha" in page_text.lower() and "productTitle" not in page_text:
            result["error"] = "遇到验证码页面，需人工处理"
            return result

        soup = BeautifulSoup(page_text, "lxml")

        result["title"] = _parse_title(soup)
        result["rating"] = _parse_rating(soup)
        result["review_count"] = _parse_review_count(soup, page_text)

        if result["rating"] is None and result["review_count"] is None:
            result["error"] = "未能解析到星级和评论数，页面结构可能已变更"

    except requests.errors.RequestsError as e:
        result["error"] = f"网络请求失败: {e}"
    except Exception as e:
        result["error"] = f"未知错误: {type(e).__name__}: {e}"

    return result


def fetch_all_products(
    product_urls: list[str],
    interval_min: int = 3,
    interval_max: int = 6,
    timeout: int = 15,
    max_retries: int = 3,
) -> list[dict]:
    """批量抓取所有产品的评论数据"""
    results = []

    for i, url in enumerate(product_urls):
        logger.info(f"正在抓取 ({i+1}/{len(product_urls)}): {url}")

        result = None
        for attempt in range(max_retries):
            if attempt > 0:
                wait = 2 ** attempt
                logger.info(f"  重试 {attempt}/{max_retries - 1}，等待 {wait} 秒...")
                time.sleep(wait)

            result = fetch_product(url, timeout=timeout)

            if result["error"] is None:
                break
            if "404" in str(result.get("error", "")):
                break

        results.append(result)

        if result["error"]:
            logger.warning(f"  抓取失败 ({url}): {result['error']}")
        else:
            logger.info(
                f"  成功: {result['title'][:40]}... | *{result['rating']} | {result['review_count']} reviews"
            )

        if i < len(product_urls) - 1:
            delay = random.uniform(interval_min, interval_max)
            logger.debug(f"  等待 {delay:.1f} 秒...")
            time.sleep(delay)

    return results
