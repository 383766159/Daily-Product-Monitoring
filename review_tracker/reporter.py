"""报告生成模块 - 生成 HTML 格式的每日对比报告（全内联样式，兼容 QQ/Gmail）"""

from datetime import date


def _fmt_change(val):
    if val is None:
        return "-"
    if val > 0:
        return f'<span style="color:#d32f2f;font-weight:bold;">+{val}</span>'
    elif val < 0:
        return f'<span style="color:#2e7d32;font-weight:bold;">{val}</span>'
    return "0"


def _num(val):
    if val is None:
        return "-"
    if isinstance(val, float):
        return f"{val:.1f}"
    return f"{val:,}"


def build_report(comparison_data, report_date, total, errors):
    has_prev = any(not r["is_new"] for r in comparison_data)
    changed_count = sum(
        1 for r in comparison_data
        if not r["is_new"] and not r["has_error"] and (
            (r.get("rating_change") is not None and r["rating_change"] != 0)
            or (r.get("reviews_change") is not None and r["reviews_change"] != 0)
        )
    )

    rows_html = ""
    for r in comparison_data:
        if r["has_error"]:
            row_bg = "background:#ffebee;"
        elif not r["is_new"] and (
            (r.get("rating_change") is not None and r["rating_change"] != 0)
            or (r.get("reviews_change") is not None and r["reviews_change"] != 0)
        ):
            row_bg = "background:#fff8e1;"
        else:
            row_bg = ""

        td = "padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;vertical-align:middle;"
        lnk = "color:#1565c0;text-decoration:none;"
        display_title = r.get("asin", "")

        if r["has_error"]:
            rows_html += (
                f'<tr style="{row_bg}">'
                f'<td style="{td}"><a href="{r["url"]}" style="{lnk}" target="_blank">{display_title}</a></td>'
                f'<td style="{td}color:#c62828;" colspan="2">获取失败</td>'
                f'<td style="{td}color:#c62828;" colspan="2">获取失败</td>'
                f'<td style="{td}">-</td><td style="{td}">-</td></tr>'
            )
        elif r["is_new"]:
            rows_html += (
                f'<tr style="{row_bg}">'
                f'<td style="{td}"><a href="{r["url"]}" style="{lnk}" target="_blank">{display_title}</a></td>'
                f'<td style="{td}">{_num(r["rating_today"])}</td>'
                f'<td style="{td}">{_num(r["reviews_today"])}</td>'
                f'<td style="{td}color:#888;" colspan="2">首次记录</td>'
                f'<td style="{td}">-</td><td style="{td}">-</td></tr>'
            )
        else:
            rows_html += (
                f'<tr style="{row_bg}">'
                f'<td style="{td}"><a href="{r["url"]}" style="{lnk}" target="_blank">{display_title}</a></td>'
                f'<td style="{td}">{_num(r["rating_today"])}</td>'
                f'<td style="{td}">{_num(r["reviews_today"])}</td>'
                f'<td style="{td}">{_num(r["rating_yesterday"])}</td>'
                f'<td style="{td}">{_num(r["reviews_yesterday"])}</td>'
                f'<td style="{td}">{_fmt_change(r.get("rating_change"))}</td>'
                f'<td style="{td}">{_fmt_change(r.get("reviews_change"))}</td></tr>'
            )

    summary_parts = [f"共跟踪 <b>{total}</b> 个产品"]
    if errors > 0:
        summary_parts.append(f"其中 <b>{errors}</b> 个获取失败")
    if has_prev:
        summary_parts.append(f"<b>{changed_count}</b> 个有变化")
    else:
        summary_parts.append("首次运行，暂无对比数据")
    summary_text = "，".join(summary_parts)

    th = "padding:10px 12px;border-bottom:2px solid #ddd;font-size:12px;color:#666;text-align:left;"
    if not has_prev:
        header_html = (
            f'<tr style="background:#fafafa;">'
            f'<th style="{th}">产品</th>'
            f'<th style="{th}">当前星级</th>'
            f'<th style="{th}">当前评论数</th>'
            f'<th style="{th}" colspan="2">对比昨日</th>'
            f'<th style="{th}">星级变化</th>'
            f'<th style="{th}">评论变化</th></tr>'
        )
    else:
        header_html = (
            f'<tr style="background:#fafafa;">'
            f'<th style="{th}">产品</th>'
            f'<th style="{th}">今日星级</th>'
            f'<th style="{th}">今日评论</th>'
            f'<th style="{th}">昨日星级</th>'
            f'<th style="{th}">昨日评论</th>'
            f'<th style="{th}">星级变化</th>'
            f'<th style="{th}">评论变化</th></tr>'
        )

    html = (
        '<!DOCTYPE html>\n<html>\n'
        '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>\n'
        '<body style="margin:0;padding:20px;background:#f5f5f5;font-family:Arial,sans-serif;">\n'
        '<table role="presentation" style="max-width:680px;width:100%;margin:0 auto;background:#fff;border-radius:6px;" cellpadding="0" cellspacing="0" border="0">\n'
        '<tr><td style="background:#232f3e;padding:20px 24px;border-radius:6px 6px 0 0;">'
        '<h1 style="margin:0;font-size:18px;color:#fff;font-weight:600;">Amazon Review Tracker</h1>'
        f'<p style="margin:4px 0 0;color:rgba(255,255,255,0.7);font-size:13px;">{report_date}</p></td></tr>\n'
        f'<tr><td style="padding:14px 24px;background:#fff8e1;border-bottom:1px solid #ffe082;font-size:13px;color:#5d4037;">{summary_text}</td></tr>\n'
        '<tr><td style="padding:0;">'
        '<table role="presentation" style="width:100%;border-collapse:collapse;" cellpadding="0" cellspacing="0" border="0">\n'
        f'{header_html}\n{rows_html}\n'
        '</table></td></tr>\n'
        f'<tr><td style="padding:14px 24px;font-size:11px;color:#999;text-align:center;border-top:1px solid #eee;">Amazon Review Tracker . Daily Report . {report_date}</td></tr>\n'
        '</table>\n</body>\n</html>'
    )

    return html
