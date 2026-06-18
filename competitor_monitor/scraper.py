"""竞品监控 - 主抓取模块"""
import sys
import os
import random
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.fetcher import fetch_with_retry, is_captcha, is_unavailable
from competitor_monitor.extractors import (
    extract_brand,
    extract_strike_price,
    extract_page_price,
    extract_rating,
    extract_review_count,
    extract_rank,
    extract_buy_box_seller,
    extract_inventory,
    extract_promotions,
    extract_variation_count,
    extract_other,
)

logger = logging.getLogger(__name__)

AMAZON_DP_BASE = "https://www.amazon.com/dp/"


def scrape_asin(asin: str, timeout: int = 20, max_retries: int = 3) -> dict:
    url = f"{AMAZON_DP_BASE}{asin}"

    def _new_snapshot(err: str | None = None) -> dict:
        return {
            "asin": asin,
            "brand": "", "strike_price": "", "page_price": "",
            "promotions": "", "rating": "", "review_count": "",
            "rank": "", "variation_count": "", "inventory": "",
            "buy_box_seller": "", "other": "/",
            "ok": False, "error": err,
        }

    soup = fetch_with_retry(url, max_retries=max_retries, timeout=timeout, interval=3.0)

    if soup is None:
        return _new_snapshot("网络请求失败（可能触发反爬）")

    if is_captcha(soup):
        return _new_snapshot("命中 Amazon 验证码")

    if is_unavailable(soup):
        return _new_snapshot("页面不可用或已下架")

    brand = extract_brand(soup)
    strike_price = extract_strike_price(soup)
    page_price = extract_page_price(soup)
    promotions = extract_promotions(soup) or "/"
    rating = extract_rating(soup)
    review_count = extract_review_count(soup)
    rank = extract_rank(soup)
    variation_count = extract_variation_count(soup)
    inventory = extract_inventory(soup)
    buy_box_seller = extract_buy_box_seller(soup)
    other = extract_other(soup)

    error = None
    if not page_price:
        error = "页面价格为空"

    return {
        "asin": asin,
        "brand": brand,
        "strike_price": strike_price,
        "page_price": page_price,
        "promotions": promotions,
        "rating": rating,
        "review_count": review_count,
        "rank": rank,
        "variation_count": variation_count,
        "inventory": inventory,
        "buy_box_seller": buy_box_seller,
        "other": other,
        "ok": error is None,
        "error": error,
    }


def scrape_asins(
    asins: list[str],
    interval_min: int = 5,
    interval_max: int = 10,
    timeout: int = 20,
    max_retries: int = 3,
) -> list[dict]:
    """批量抓取 ASIN"""
    results = []
    total = len(asins)

    for i, asin in enumerate(asins):
        logger.info(f"Scraping ({i+1}/{total}): {asin}")
        snapshot = scrape_asin(asin, timeout=timeout, max_retries=max_retries)

        if snapshot["ok"]:
            logger.info(
                f"  OK: {snapshot['brand'][:15]} | "
                f"${snapshot['page_price']} | "
                f"Star {snapshot['rating']} | "
                f"{snapshot['review_count']} reviews | "
                f"{snapshot['inventory']}"
            )
        else:
            logger.warning(f"  FAIL: {snapshot['error']}")
            # 失败后额外等待，避免连续触发反爬
            time.sleep(5)

        results.append(snapshot)

        if i < total - 1:
            delay = random.uniform(interval_min, interval_max)
            time.sleep(delay)

    return results
