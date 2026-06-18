"""AC标签 + 阶梯折扣提取器"""
from bs4 import BeautifulSoup


def extract_ac_badge(soup: BeautifulSoup) -> bool:
    """是否 Amazon's Choice"""
    selectors = [
        ".mvt-ac-badge-rectangle",
        '[data-hook="amzn-choice-badge"]',
        "#acBadge_feature_div .a-badge-label",
        '[class*="ac-badge"] span',
    ]
    for sel in selectors:
        try:
            els = soup.select(sel)
            for el in els:
                txt = el.get_text(strip=True).lower()
                if "amazon" in txt and ("choice" in txt):
                    return True
        except Exception:
            pass
    return False


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
        parts.append(f"阶梯:{tier}")
    return "；".join(parts) if parts else "/"
