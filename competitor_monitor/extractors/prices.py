"""价格提取器 (修复：限定 Buy Box 区域)"""
from bs4 import BeautifulSoup


def extract_strike_price(soup: BeautifulSoup) -> str:
    """划线价 - 仅在 Buy Box 区域查找"""
    # 只取主购买区域的划线价
    buybox = soup.select_one("#desktop_buybox, #buybox, #apex_desktop")
    if not buybox:
        buybox = soup

    # 优先 basisPrice
    el = buybox.select_one("span.basisPrice .a-offscreen")
    if el:
        return el.get_text(strip=True)

    # 其次 .a-text-price
    el = buybox.select_one(".a-text-price span.a-offscreen")
    if el:
        return el.get_text(strip=True)

    # 最后 data-a-strike
    el = buybox.select_one("span[data-a-strike='true'] .a-offscreen")
    if el:
        return el.get_text(strip=True)

    return ""


def extract_page_price(soup: BeautifulSoup) -> str:
    """页面当前主价格 - 仅主价格区域"""
    buybox = soup.select_one("#desktop_buybox, #buybox, #apex_desktop, #corePrice_feature_div")
    if not buybox:
        buybox = soup

    whole = buybox.select_one(".a-price-whole")
    fraction = buybox.select_one(".a-price-fraction")
    if not whole:
        return ""
    w = whole.get_text(strip=True).rstrip(".")
    f = fraction.get_text(strip=True) if fraction else "00"
    return f"{w}.{f}"
