"""卖家提取器"""
from bs4 import BeautifulSoup


def extract_buy_box_seller(soup: BeautifulSoup) -> str:
    el = soup.select_one("#sellerProfileTriggerId, #merchantInfo_feature_div .a-size-small")
    return el.get_text(strip=True) if el else ""
