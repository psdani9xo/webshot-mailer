from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SmtpProfile(db.Model):
    __tablename__ = "smtp_profiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    host = db.Column(db.String(200), nullable=False)
    port = db.Column(db.Integer, nullable=False, default=587)
    encryption = db.Column(db.String(20), nullable=False, default="STARTTLS")  # STARTTLS|SSL|NONE

    username = db.Column(db.String(200), nullable=False)
    password_env = db.Column(db.String(200), nullable=False)  # nombre de la variable de entorno

    from_email = db.Column(db.String(200), nullable=False)
    reply_to = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    timezone = db.Column(db.String(60), nullable=False, default="Europe/Madrid")

    schedule_type = db.Column(db.String(20), nullable=False, default="DAILY")  # DAILY|WEEKLY|INTERVAL
    time_hhmm = db.Column(db.String(5), nullable=True)  # "08:30"
    weekdays = db.Column(db.String(50), nullable=True)  # "1,2,3,4,5" (lun=1..dom=7)
    interval_minutes = db.Column(db.Integer, nullable=True)

    url = db.Column(db.Text, nullable=False)

    viewport_width = db.Column(db.Integer, default=1920)
    viewport_height = db.Column(db.Integer, default=5000)
    full_page = db.Column(db.Boolean, default=False)

    device_scale_factor = db.Column(db.Float, default=1.0)
    css_zoom = db.Column(db.Float, default=1.0)

    wait_mode = db.Column(db.String(20), default="SLEEP")  # SLEEP|SELECTOR
    wait_seconds = db.Column(db.Integer, default=5)
    wait_selector = db.Column(db.String(300), nullable=True)

    remove_selectors = db.Column(db.Text, default="[]")  # JSON array string
    pre_js = db.Column(db.Text, nullable=True)

    image_format = db.Column(db.String(10), default="PNG")  # PNG|JPEG
    jpeg_quality = db.Column(db.Integer, nullable=True)
    max_width = db.Column(db.Integer, nullable=True)

    smtp_profile_id = db.Column(db.Integer, db.ForeignKey("smtp_profiles.id"), nullable=False)
    smtp_profile = db.relationship("SmtpProfile")

    to_emails = db.Column(db.Text, nullable=False)   # csv
    cc_emails = db.Column(db.Text, nullable=True)
    bcc_emails = db.Column(db.Text, nullable=True)

    subject_template = db.Column(db.String(300), default="Captura {task_name} {date} {time}")
    html_template = db.Column(db.Text, default="""<html><body>
<h2>Captura</h2>
<p>{url}</p>
<img src="cid:screenshot" style="max-width:100%; border:1px solid #ddd; padding:10px;"/>
</body></html>""")
    text_template = db.Column(db.Text, nullable=True)

    attach_inline = db.Column(db.Boolean, default=True)
    attach_file = db.Column(db.Boolean, default=False)

    retention_days = db.Column(db.Integer, default=14)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Run(db.Model):
    __tablename__ = "runs"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    task = db.relationship("Task")

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(10), default="ERROR")  # OK|ERROR
    error_message = db.Column(db.Text, nullable=True)

    screenshot_path = db.Column(db.Text, nullable=True)
    image_bytes = db.Column(db.Integer, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    trigger = db.Column(db.String(20), default="SCHEDULED")  # SCHEDULED|MANUAL_TEST|MANUAL_CAPTURE
