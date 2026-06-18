"""邮件发送模块 - 通过 SMTP 发送 HTML 报告"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

logger = logging.getLogger(__name__)


def send_report(
    html_body: str,
    report_date: str,
    smtp_host: str,
    smtp_port: int,
    sender: str,
    password: str,
    recipient: str,
) -> bool:
    """发送 HTML 格式的邮件报告

    Args:
        html_body: HTML 邮件正文
        report_date: 日期字符串，用于邮件标题
        smtp_host: SMTP 服务器地址
        smtp_port: SMTP 端口（587 for TLS）
        sender: 发件人邮箱
        password: SMTP 密码 / 应用专用密码
        recipient: 收件人邮箱

    Returns:
        bool: 发送成功返回 True
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"📦 亚马逊评论追踪日报 - {report_date}", "utf-8")
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        logger.info(f"正在连接 SMTP 服务器 {smtp_host}:{smtp_port} ...")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        logger.info(f"邮件发送成功 → {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP 认证失败，请检查邮箱和密码（Gmail 需使用应用专用密码）")
        return False
    except smtplib.SMTPConnectError:
        logger.error(f"无法连接 SMTP 服务器 {smtp_host}:{smtp_port}")
        return False
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False
