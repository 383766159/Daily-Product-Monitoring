"""竞品监控 - 主入口

用法:
    python -m competitor_monitor.monitor              # 执行每日抓取+写入 Excel
    python -m competitor_monitor.monitor --dry-run    # 仅抓取和打印结果，不写 Excel
"""
import sys
import os
import io
import logging

# 确保项目根目录在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import yaml
from datetime import date

from competitor_monitor.scraper import scrape_asins
from competitor_monitor.excel_writer import write_snapshots

# UTF-8 stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("monitor")


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(dry_run: bool = False):
    config = load_config()
    asins = config["asins"]
    scraper_cfg = config.get("scraper", {})
    output_dir = config.get("output_dir", "outputs")

    if not asins:
        logger.error("config.yaml 中未配置 ASIN 列表")
        return

    logger.info(f"{'='*60}")
    logger.info(f"Competitor Monitor - {len(asins)} ASINs")
    logger.info(f"{'='*60}")

    # 抓取
    results = scrape_asins(
        asins=asins,
        interval_min=scraper_cfg.get("interval_min", 3),
        interval_max=scraper_cfg.get("interval_max", 6),
        timeout=scraper_cfg.get("timeout", 20),
        max_retries=scraper_cfg.get("max_retries", 3),
    )

    ok_count = sum(1 for r in results if r["ok"])
    logger.info(f"Done: {ok_count}/{len(results)} OK")

    if dry_run:
        logger.info("Dry-run mode, skipping Excel write")
        # 打印摘要
        for r in results:
            if r["ok"]:
                print(f"  [{r['asin']}] {r['brand']} | ${r['page_price']} | "
                      f"Star {r['rating']} | {r['review_count']} reviews | "
                      f"{r['inventory']} | {r['rank'][:40]}")
            else:
                print(f"  [{r['asin']}] FAIL: {r['error']}")
    else:
        # Excel 输出路径
        output_path = os.path.join(
            os.path.dirname(__file__), output_dir, f"monitor_{date.today().strftime('%Y%m')}.xlsx"
        )
        write_snapshots(output_path, asins, results)
        logger.info(f"Report written to {output_path}")


def main():
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)


if __name__ == "__main__":
    main()
