"""AC标签 + 阶梯折扣提取器"""
from bs4 import BeautifulSoup


def extract_ac_badge(soup: BeautifulSoup) -> bool:
    """是否 Amazon's Choice"""
    ac = soup.select_one("[data-hook='amzn-choice-badge'], #acBadge_feature_div .a-badge-label")
    return ac is not None


def extract_tier_discount(soup: BeautifulSoup) -> str:
    """阶梯折扣"""
    el = soup.select_one("#tieredDiscount, .tiered-discount")
    return el.get_text(strip=True) if el else ""


def extract_other(soup: BeautifulSoup) -> str:
    """其他：AC + 阶梯折扣"""
    parts = []
    if extract_ac_badge(soup):
        parts.append("AC")
    tier = extract_tier_discount(soup)
    if tier:
        parts.append(f"\u9636\u68af:{tier}")  # 阶梯:xxx
    return "\uff1b".join(parts) if parts else "/"  # ；分隔
