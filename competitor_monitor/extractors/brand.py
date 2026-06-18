"""品牌提取器"""
from bs4 import BeautifulSoup


def extract_brand(soup: BeautifulSoup) -> str:
    el = soup.select_one("#bylineInfo")
    if not el:
        return ""
    text = el.get_text(strip=True)
    # 去掉 "Brand: " / "Visit the " / " Store" 前缀后缀
    text = text.replace("Brand:", "").replace("Visit the", "").replace("Store", "").strip()
    return text
