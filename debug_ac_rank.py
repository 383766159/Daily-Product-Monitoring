import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from shared.fetcher import fetch_page
from bs4 import BeautifulSoup
import re

for asin in ["B09YGT8CZ5", "B09WHV1NJL", "B0DY4S3HP2"]:
    soup = fetch_page(f"https://www.amazon.com/dp/{asin}")
    if not soup:
        print(f"\n[{asin}] FETCH FAILED")
        continue

    print(f"\n[{asin}]")

    # --- AC badge check ---
    ac_selectors = [
        '[data-hook="amzn-choice-badge"]',
        '#acBadge_feature_div .a-badge-label',
        '.mvt-ac-badge-rectangle',
        '.ac-badge',
        '[class*="ac-badge"]',
        'span:contains("Amazon")',
    ]
    for sel in ac_selectors:
        try:
            els = soup.select(sel)
            if els:
                for el in els:
                    txt = el.get_text(strip=True)
                    if "amazon" in txt.lower() or "choice" in txt.lower():
                        print(f"  AC found! selector={sel} -> [{txt}]")
        except:
            pass

    # Also search raw text
    if "amazon's choice" in soup.get_text().lower():
        print("  AC found in page text!")
        # Find the element
        for el in soup.find_all(["span", "div"]):
            txt = el.get_text(strip=True).lower()
            if "amazon's choice" in txt or "amazon choice" in txt:
                print(f"  AC element: <{el.name} class='{el.get('class','')}'> [{el.get_text(strip=True)[:80]}]")
                break

    # --- Rank check ---
    for area in soup.select("#detailBullets_feature_div li, .detail-bullet-list li"):
        text = area.get_text(" ", strip=True)
        if re.search(r"Best Sellers? Rank|销售排行榜", text, re.IGNORECASE):
            print(f"  Rank found in detailBullets: {text[:120]}")
            break
    else:
        # Check if detailBullets exists at all
        bullets = soup.select_one("#detailBullets_feature_div, .detail-bullet-list")
        if bullets:
            print(f"  detailBullets exists but no rank line. Content preview: {bullets.get_text(' ')[:200]}")
        else:
            print("  No detailBullets div found at all")

