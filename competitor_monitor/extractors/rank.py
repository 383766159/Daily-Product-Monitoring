"""排名提取器 - 提取 #大类#小类 格式"""
from bs4 import BeautifulSoup
import re


def extract_rank(soup: BeautifulSoup) -> str:
    """产品排名，返回格式: #大类排名#小类排名"""

    raw = ""
    for area in soup.select("#detailBullets_feature_div li, .detail-bullet-list li"):
        text = area.get_text(" ", strip=True)
        if re.search(r"Best Sellers? Rank", text, re.IGNORECASE):
            raw = re.sub(r"Best Sellers? Rank[:\s]*", "", text, flags=re.IGNORECASE).strip()
            raw = raw.replace("\u00a0", " ")
            break

    if not raw:
        for row in soup.select("#prodDetails table tr, #productDetails_detailBullets_sections1 tr"):
            cells = row.select("th, td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                if "rank" in label or "best seller" in label:
                    raw = cells[1].get_text(" ", strip=True)
                    break

    if not raw:
        return ""

    # 提取所有 #数字 部分
    # 格式: "#65,534 in Home & Kitchen (...) #104 in HEPA Filter Air Purifiers"
    numbers = re.findall(r"#([\d,]+)", raw)
    if not numbers:
        return ""

    # 去掉逗号，用 # 连接
    cleaned = [n.replace(",", "") for n in numbers]
    return "#" + "#".join(cleaned)
