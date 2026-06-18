"""变体数量提取器"""
from bs4 import BeautifulSoup


def extract_variation_count(soup: BeautifulSoup) -> str:
    """变体 SKU 数量"""
    swatches = soup.select(
        '[id^="variation_"] .swatchAvailable, '
        "#twister .swatchAvailable, "
        ".a-variation .swatchAvailable"
    )
    count = len(swatches)
    return str(count) if count > 0 else ""
