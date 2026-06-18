"""竞品监控 - 主入口

用法:
    python -m competitor_monitor.monitor              # 仅写 Excel
    python -m competitor_monitor.monitor --email      # 写 Excel + 发邮件
    python -m competitor_monitor.monitor --dry-run    # 仅抓取不写 Excel
"""
import sys
import os
import io
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import yaml
from datetime import date

from competitor_monitor.scraper import scrape_asins
from competitor_monitor.excel_writer import write_snapshots

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


def send_email_report(excel_path: str, results: list[dict]):
    """发送邮件报告（带 Excel 附件 + 摘要表格）"""
    # 从 review_tracker 读取邮箱配置
    email_config_path = os.path.join(PROJECT_ROOT, "review_tracker", "config.yaml")
    if not os.path.exists(email_config_path):
        logger.error("未找到邮件配置: review_tracker/config.yaml")
        return

    with open(email_config_path, "r", encoding="utf-8") as f:
        email_cfg = yaml.safe_load(f).get("email", {})

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    from email.header import Header

    today = date.today().isoformat()
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    # 构建 HTML 摘要
    rows_html = ""
    for r in results:
        bg = "#ffebee" if not r["ok"] else ""
        rows_html += f'<tr style="background:{bg}">'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r["asin"]}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("brand","") or "/"}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("page_price","") or "/"}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("rating","") or "/"}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("review_count","") or "/"}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("rank","") or "/"}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("inventory","") or "/"}</td>'
        rows_html += f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("other","") or "/"}</td>'
        rows_html += "</tr>"

    html_body = f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;padding:20px;background:#f5f5f5;">
<div style="max-width:700px;margin:0 auto;background:#fff;border-radius:6px;">
<div style="background:#232f3e;padding:18px 24px;border-radius:6px 6px 0 0;">
<h1 style="margin:0;font-size:18px;color:#fff;">Competitor Monitor</h1>
<p style="margin:4px 0 0;color:rgba(255,255,255,0.7);font-size:13px;">{today}</p>
</div>
<div style="padding:14px 24px;background:#fff8e1;font-size:13px;">
共 {len(results)} 个产品，成功 <b>{ok_count}</b> 个
{f"，失败 <b>{fail_count}</b> 个" if fail_count > 0 else ""}
</div>
<table style="width:100%;border-collapse:collapse;" cellpadding="0" cellspacing="0">
<tr style="background:#fafafa;">
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">ASIN</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">品牌</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">价格</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">评分</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">评论</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">排名</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">库存</th>
<th style="padding:8px 10px;border-bottom:2px solid #ddd;font-size:12px;text-align:left;">其他</th>
</tr>
{rows_html}
</table>
<div style="padding:14px 24px;font-size:11px;color:#999;text-align:center;border-top:1px solid #eee;">
Excel 附件包含完整 10 项指标 · {today}
</div>
</div>
</body>
</html>"""

    msg = MIMEMultipart()
    msg["Subject"] = Header(f"Competitor Monitor - {today}", "utf-8")
    msg["From"] = email_cfg["sender"]
    msg["To"] = email_cfg["recipient"]
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # 附加 Excel
    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(excel_path)}"',
            )
            msg.attach(part)

    try:
        with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"], timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_cfg["sender"], email_cfg["password"])
            server.sendmail(email_cfg["sender"], email_cfg["recipient"], msg.as_string())
        logger.info(f"Email sent to {email_cfg['recipient']}")
    except Exception as e:
        logger.error(f"Email failed: {e}")


def run(dry_run: bool = False, send_email: bool = False):
    config = load_config()
    asins = config["asins"]
    scraper_cfg = config.get("scraper", {})
    output_dir = config.get("output_dir", "outputs")

    if not asins:
        logger.error("No ASINs configured")
        return

    logger.info(f"{'='*60}")
    logger.info(f"Competitor Monitor - {len(asins)} ASINs")
    logger.info(f"{'='*60}")

    results = scrape_asins(
        asins=asins,
        interval_min=scraper_cfg.get("interval_min", 5),
        interval_max=scraper_cfg.get("interval_max", 10),
        timeout=scraper_cfg.get("timeout", 20),
        max_retries=scraper_cfg.get("max_retries", 3),
    )

    ok_count = sum(1 for r in results if r["ok"])
    logger.info(f"Done: {ok_count}/{len(results)} OK")

    if dry_run:
        logger.info("Dry-run mode, skipping Excel write")
        for r in results:
            if r["ok"]:
                print(f"  [{r['asin']}] {r['brand']} | ${r['page_price']} | "
                      f"Star {r['rating']} | {r['review_count']} reviews | "
                      f"{r['inventory']} | {r['other']}")
            else:
                print(f"  [{r['asin']}] FAIL: {r['error']}")
    else:
        output_path = os.path.join(
            os.path.dirname(__file__), output_dir, f"monitor_{date.today().strftime('%Y%m')}.xlsx"
        )
        write_snapshots(output_path, asins, results)
        logger.info(f"Report written to {output_path}")

        if send_email:
            send_email_report(output_path, results)


def main():
    dry_run = "--dry-run" in sys.argv
    send_email = "--email" in sys.argv
    run(dry_run=dry_run, send_email=send_email)


if __name__ == "__main__":
    main()
