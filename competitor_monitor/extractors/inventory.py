"""库存提取器"""
from bs4 import BeautifulSoup
import re


def extract_inventory(soup: BeautifulSoup) -> str:
    """库存状态：限购N / 仅剩N / 充足 / /"""

    # 1. 数量下拉框最大值
    select = soup.select_one(
        'select#quantity, select[name="quantity"], select[id*="quantity"], select.a-native-dropdown'
    )
    if select:
        max_val = 0
        for opt in select.select("option"):
            try:
                v = int(opt.get("value", 0))
                if v > max_val:
                    max_val = v
            except (ValueError, TypeError):
                pass
        if max_val > 0:
            return f"\u9650\u8d2d{max_val}"  # 限购N

    # 2. "Only X left in stock"
    text = soup.get_text()
    low = re.search(r"[Oo]nly\s+(\d+)\s+left\s+in\s+stock", text)
    if low:
        return f"\u4ec5\u5269{low.group(1)}"  # 仅剩N

    # 3. In Stock -> 充足
    if re.search(r"in\s+stock", text, re.IGNORECASE):
        return "\u5145\u8db3"  # 充足

    # 4. Unavailable
    if re.search(r"currently\s+unavailable|unavailable", text, re.IGNORECASE):
        return "/"

    return "/"
