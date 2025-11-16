import os, requests, smtplib, json
from email.message import EmailMessage

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")  # https webhook
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID")
EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def send_slack(text):
    if not SLACK_WEBHOOK:
        return False
    try:
        requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=5)
        return True
    except Exception:
        return False

def send_telegram(text):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
        return True
    except Exception:
        return False

def send_email(subject, body):
    if not (SMTP_HOST and EMAIL_TO and EMAIL_FROM):
        return False
    try:
        msg = EmailMessage()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject
        msg.set_content(body)
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

def send_alert_if_needed(record):
    """
    record expected keys: symbol, boosted_score, decision
    """
    try:
        boosted = float(record.get("boosted_score", 0) or 0)
    except Exception:
        boosted = 0
    if boosted >= float(os.getenv("ALERT_THRESHOLD", "78")):
        text = f"[IOA ALERT] {record.get('symbol')} boosted={boosted} decision={record.get('decision')}"
        # send to configured channels
        send_slack(text)
        send_telegram(text)
        send_email(f"IOA Alert: {record.get('symbol')}", text)
        return True
    return False
