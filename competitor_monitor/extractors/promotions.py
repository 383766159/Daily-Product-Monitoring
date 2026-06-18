"""活动/促销提取器"""
from bs4 import BeautifulSoup


def extract_promotions(soup: BeautifulSoup) -> str:
    """优惠券 / 促销标签"""
    parts = []

    # Coupon
    coupon = soup.select_one("#couponText, .promoPriceBadge, [data-hook='coupon-badge']")
    if coupon:
        parts.append(coupon.get_text(strip=True))

    # Deal badge
    deal = soup.select_one("#dealBadge_feature_div, .deal-badge, [data-hook='deal-badge']")
    if deal:
        parts.append(deal.get_text(strip=True))

    # Lightning Deal
    ld = soup.select_one("#lightningDeal, .lightning-deal-badge")
    if ld:
        parts.append(ld.get_text(strip=True))

    return " ".join(parts).replace("\n", " ").strip() if parts else ""
