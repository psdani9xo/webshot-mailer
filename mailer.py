import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate

def _split_emails(csv_text: str):
    if not csv_text:
        return []
    return [e.strip() for e in csv_text.split(",") if e.strip()]

def send_email_with_screenshot(task, smtp_profile, screenshot_path: str):
    password = os.getenv(smtp_profile.password_env, "")
    if not password:
        raise RuntimeError(f"No existe la variable de entorno {smtp_profile.password_env} o esta vacia")

    to_list = _split_emails(task.to_emails)
    cc_list = _split_emails(task.cc_emails or "")
    bcc_list = _split_emails(task.bcc_emails or "")
    all_rcpt = to_list + cc_list + bcc_list
    if not all_rcpt:
        raise RuntimeError("No hay destinatarios")

    msg = MIMEMultipart("related")
    msg["From"] = smtp_profile.from_email
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if smtp_profile.reply_to:
        msg["Reply-To"] = smtp_profile.reply_to
    msg["Date"] = formatdate(localtime=True)

    # subject + body vars
    from datetime import datetime
    now = datetime.now()
    subject = (task.subject_template or "Captura").format(
        task_name=task.name,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M"),
        url=task.url,
    )
    msg["Subject"] = subject

    html = (task.html_template or "").format(
        task_name=task.name,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M"),
        url=task.url,
    )
    alt = MIMEMultipart("alternative")
    if task.text_template:
        alt.attach(MIMEText(task.text_template, "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)

    # attach inline
    with open(screenshot_path, "rb") as f:
        img = MIMEImage(f.read(), name=os.path.basename(screenshot_path))
    img.add_header("Content-ID", "<screenshot>")
    img.add_header("Content-Disposition", "inline", filename=os.path.basename(screenshot_path))
    msg.attach(img)

    # optional: also attach file (non-inline)
    if task.attach_file:
        with open(screenshot_path, "rb") as f:
            img2 = MIMEImage(f.read(), name=os.path.basename(screenshot_path))
        img2.add_header("Content-Disposition", "attachment", filename=os.path.basename(screenshot_path))
        msg.attach(img2)

    # connect
    enc = (smtp_profile.encryption or "STARTTLS").upper()
    host, port = smtp_profile.host, int(smtp_profile.port)

    if enc == "SSL":
        server = smtplib.SMTP_SSL(host, port, timeout=30)
    else:
        server = smtplib.SMTP(host, port, timeout=30)

    try:
        server.ehlo()
        if enc == "STARTTLS":
            server.starttls()
            server.ehlo()

        server.login(smtp_profile.username, password)
        server.sendmail(smtp_profile.from_email, all_rcpt, msg.as_string())
    finally:
        try:
            server.quit()
        except Exception:
            pass
