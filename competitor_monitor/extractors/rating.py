"""评分提取器"""
from bs4 import BeautifulSoup
import re


def normalize_rating(text: str) -> str:
    """从各种格式中提取评分数字"""
    text = text.replace("\u00a0", " ").strip()
    patterns = [
        r"(\d+(?:[.,]\d+)?)\s*out of\s*5",
        r"(\d+(?:[.,]\d+)?)\s*(?:von|sur|su|de)\s*5",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).replace(",", ".")
    m = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return m.group(1).replace(",", ".") if m else ""


def extract_rating(soup: BeautifulSoup) -> str:
    """星级"""
    # 优先用 data-hook，它的 text 最干净
    el = soup.select_one('[data-hook="rating-out-of-text"]')
    if el:
        result = normalize_rating(el.get_text(strip=True))
        if result:
            return result

    # 备选 a-icon-alt
    span = soup.select_one("span.a-icon-alt")
    if span:
        result = normalize_rating(span.get_text(strip=True))
        if result:
            return result

    # 最后尝试 acrPopover（aria-label）
    pop = soup.select_one("#acrPopover")
    if pop:
        aria = pop.get("aria-label", "")
        result = normalize_rating(aria)
        if result:
            return result

    return ""


def extract_review_count(soup: BeautifulSoup) -> str:
    """评论数（纯数字）"""
    el = (
        soup.select_one("#acrCustomerReviewText, [data-hook='total-review-count']")
        or soup.select_one("a#acrCustomerReviewLink")
    )
    if not el:
        return ""
    digits = re.sub(r"[^\d]", "", el.get_text(strip=True))
    return digits
