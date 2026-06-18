"""排名提取器"""
from bs4 import BeautifulSoup
import re


def extract_rank(soup: BeautifulSoup) -> str:
    """产品排名（大类/小类）"""
    # 查找 detail bullets 区域
    for area in soup.select("#detailBullets_feature_div li, .detail-bullet-list li"):
        text = area.get_text(" ", strip=True)
        if re.search(r"Best Sellers? Rank", text, re.IGNORECASE):
            rank = re.sub(r"Best Sellers? Rank[:\s]*", "", text, flags=re.IGNORECASE).strip()
            # 清理 (See Top 100...) 等冗余
            rank = re.sub(r"\s*\(See\s+Top\s+100[^)]*\)", "", rank, flags=re.IGNORECASE).strip()
            rank = rank.replace("\u00a0", " ")
            return rank

    # prodDetails 表格格式
    for row in soup.select("#prodDetails table tr, #productDetails_detailBullets_sections1 tr"):
        cells = row.select("th, td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            if "rank" in label or "best seller" in label:
                return cells[1].get_text(" ", strip=True)

    return ""
