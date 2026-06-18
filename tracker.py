"""亚马逊评论追踪系统 - 主入口

用法:
    python tracker.py              # 执行每日抓取+报告+邮件
    python tracker.py --dry-run    # 仅抓取和显示报告，不发送邮件
    python tracker.py --test       # 测试邮件发送
"""
import sys
import io
import logging
from datetime import date, timedelta
from pathlib import Path

import yaml

from scraper import fetch_all_products
from storage import Storage
from reporter import build_report
from mailer import send_report

# 修复 Windows 控制台 GBK 编码问题
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tracker")


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    path = Path(config_path)
    if not path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        logger.error("配置文件为空")
        sys.exit(1)

    products = config.get("products", [])
    if not products:
        logger.error("配置文件中未设置任何产品链接，请在 config.yaml 的 products 列表中添加")
        sys.exit(1)

    return config


def test_email(config: dict):
    """测试邮件发送"""
    email_cfg = config["email"]
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h2>测试邮件</h2>
<p>这是一封来自亚马逊评论追踪系统的测试邮件。</p>
<p>如果你收到这封邮件，说明 SMTP 配置正确！</p>
</body></html>"""
    result = send_report(
        html_body=html,
        report_date="测试",
        smtp_host=email_cfg["smtp_host"],
        smtp_port=email_cfg["smtp_port"],
        sender=email_cfg["sender"],
        password=email_cfg["password"],
        recipient=email_cfg["recipient"],
    )
    if result:
        logger.info("测试邮件发送成功！请检查收件箱。")
    else:
        logger.error("测试邮件发送失败，请查看上方日志排查原因。")


def run(dry_run: bool = False):
    """主流程"""
    logger.info("=" * 60)
    logger.info("亚马逊评论追踪系统启动")
    logger.info("=" * 60)

    # 1. 加载配置
    config = load_config()
    scraper_cfg = config.get("scraper", {})
    email_cfg = config["email"]

    product_urls = [p["url"] for p in config["products"]]

    # 2. 初始化数据库
    db = Storage()

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    logger.info(f"报告日期: {today_str}")
    logger.info(f"跟踪产品数: {len(product_urls)}")

    # 3. 抓取产品数据
    logger.info("开始抓取产品数据...")
    results = fetch_all_products(
        product_urls=product_urls,
        interval_min=scraper_cfg.get("request_interval_min", 3),
        interval_max=scraper_cfg.get("request_interval_max", 6),
        timeout=scraper_cfg.get("timeout", 15),
        max_retries=scraper_cfg.get("max_retries", 3),
    )

    # 4. 保存快照
    db.save_snapshots_batch(results, today_str)

    # 5. 生成对比报告
    comparison = db.get_comparison(today_str, yesterday_str)
    error_count = sum(1 for r in results if r.get("error"))
    success_count = len(results) - error_count

    html = build_report(
        comparison_data=comparison,
        report_date=today_str,
        total=len(results),
        errors=error_count,
    )

    # 6. 输出摘要
    logger.info("=" * 60)
    logger.info(f"抓取完成: 成功 {success_count} / {len(results)}")
    if error_count > 0:
        for r in results:
            if r.get("error"):
                logger.warning(f"  - {r['asin']}: {r['error']}")

    # 7. 统计变化
    has_changes = False
    for r in comparison:
        if not r["is_new"] and not r["has_error"]:
            r_change = r.get("rating_change")
            v_change = r.get("reviews_change")
            if (r_change is not None and r_change != 0) or (v_change is not None and v_change != 0):
                has_changes = True
                logger.info(
                    f"  {r['title'][:40]}: "
                    f"Star {r['rating_yesterday']} -> {r['rating_today']} "
                    f"({r_change:+.1f}), "
                    f"Reviews {r['reviews_yesterday']} -> {r['reviews_today']} "
                    f"({v_change:+d})"
                )

    if not has_changes and comparison:
        logger.info("  所有产品无变化")

    # 8. 发送邮件（或保存到本地）
    if dry_run:
        report_path = Path(f"report_{today_str}.html")
        report_path.write_text(html, encoding="utf-8")
        logger.info(f"Dry-run 模式：报告已保存到 {report_path.resolve()}")
        logger.info(f"报告已保存: {report_path.resolve()}")
    else:
        logger.info("发送邮件报告...")
        result = send_report(
            html_body=html,
            report_date=today_str,
            smtp_host=email_cfg["smtp_host"],
            smtp_port=email_cfg["smtp_port"],
            sender=email_cfg["sender"],
            password=email_cfg["password"],
            recipient=email_cfg["recipient"],
        )
        if result:
            logger.info("报告已发送到邮箱，请查收！")
        else:
            logger.error("邮件发送失败，请检查邮箱配置。")
            report_path = Path(f"report_{today_str}.html")
            report_path.write_text(html, encoding="utf-8")
            logger.info(f"报告已保存到本地: {report_path.resolve()}")


def main():
    args = sys.argv[1:]

    if "--test" in args:
        config = load_config()
        test_email(config)
    elif "--dry-run" in args:
        run(dry_run=True)
    else:
        run(dry_run=False)


if __name__ == "__main__":
    main()
