import os
import time
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from config import Config
from models import db, Task, Run, SmtpProfile
from scheduler import build_scheduler
from capture import capture_screenshot
from mailer import send_email_with_screenshot

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    os.makedirs(app.config["CAPTURES_DIR"], exist_ok=True)
    os.makedirs("/app/data", exist_ok=True)

    with app.app_context():
        db.create_all()

    def cleanup_old(task: Task):
        # Borra capturas viejas segun retention_days
        if not task.retention_days:
            return
        cutoff = datetime.utcnow() - timedelta(days=int(task.retention_days))
        old_runs = Run.query.filter(Run.task_id == task.id, Run.started_at < cutoff).all()
        for r in old_runs:
            if r.screenshot_path:
                try:
                    os.remove(r.screenshot_path)
                except Exception:
                    pass
            db.session.delete(r)
        db.session.commit()

    def run_task(task_id: int, trigger_name: str):
        with app.app_context():
            task = Task.query.get(task_id)
            if not task or not task.enabled:
                return

            run = Run(task_id=task.id, trigger=trigger_name, started_at=datetime.utcnow(), status="ERROR")
            db.session.add(run)
            db.session.commit()

            t0 = time.time()
            try:
                smtp = SmtpProfile.query.get(task.smtp_profile_id)
                if not smtp:
                    raise RuntimeError("No hay perfil SMTP asociado")

                screenshot_path = capture_screenshot(
                    task,
                    chrome_bin=app.config["CHROME_BIN"],
                    chromedriver_bin=app.config["CHROMEDRIVER_BIN"],
                    captures_dir=app.config["CAPTURES_DIR"],
                )

                if trigger_name != "MANUAL_CAPTURE":
                    send_email_with_screenshot(task, smtp, screenshot_path)

                run.screenshot_path = screenshot_path
                run.image_bytes = os.path.getsize(screenshot_path) if os.path.exists(screenshot_path) else None
                run.status = "OK"
                run.error_message = None
            except Exception as e:
                run.status = "ERROR"
                run.error_message = str(e)
            finally:
                run.finished_at = datetime.utcnow()
                run.duration_ms = int((time.time() - t0) * 1000)
                db.session.commit()
                cleanup_old(task)

    sched, reschedule_all = build_scheduler(app, run_task)
    sched.start()
    with app.app_context():
        reschedule_all()

    # -------- ROUTES --------

    @app.get("/")
    def index():
        tasks = Task.query.order_by(Task.id.desc()).all()
        latest = {}
        for t in tasks:
            r = Run.query.filter_by(task_id=t.id).order_by(Run.id.desc()).first()
            latest[t.id] = r
        return render_template("index.html", tasks=tasks, latest=latest)

    @app.get("/captures/<path:filename>")
    def captures(filename):
        return send_from_directory(app.config["CAPTURES_DIR"], filename)

    @app.get("/runs")
    def runs():
        task_id = request.args.get("task_id", type=int)
        q = Run.query
        if task_id:
            q = q.filter_by(task_id=task_id)
        rows = q.order_by(Run.id.desc()).limit(200).all()
        tasks = Task.query.order_by(Task.name.asc()).all()
        return render_template("runs.html", runs=rows, tasks=tasks, task_id=task_id)

    @app.get("/tasks/new")
    def task_new():
        profiles = SmtpProfile.query.order_by(SmtpProfile.name.asc()).all()
        return render_template("task_form.html", task=None, profiles=profiles)

    @app.post("/tasks/new")
    def task_new_post():
        t = Task()
        _fill_task_from_form(t, request.form)
        db.session.add(t)
        db.session.commit()
        reschedule_all()
        flash("Tarea creada", "success")
        return redirect(url_for("index"))

    @app.get("/tasks/<int:task_id>/edit")
    def task_edit(task_id):
        t = Task.query.get_or_404(task_id)
        profiles = SmtpProfile.query.order_by(SmtpProfile.name.asc()).all()
        return render_template("task_form.html", task=t, profiles=profiles)

    @app.post("/tasks/<int:task_id>/edit")
    def task_edit_post(task_id):
        t = Task.query.get_or_404(task_id)
        _fill_task_from_form(t, request.form)
        db.session.commit()
        reschedule_all()
        flash("Tarea actualizada", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def task_delete(task_id):
        t = Task.query.get_or_404(task_id)
        runs = Run.query.filter_by(task_id=t.id).all()
        for r in runs:
            if r.screenshot_path:
                try:
                    os.remove(r.screenshot_path)
                except Exception:
                    pass
            db.session.delete(r)

        db.session.delete(t)
        db.session.commit()
        reschedule_all()
        flash("Tarea eliminada", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/toggle")
    def task_toggle(task_id):
        t = Task.query.get_or_404(task_id)
        t.enabled = not t.enabled
        db.session.commit()
        reschedule_all()
        flash("Tarea activada" if t.enabled else "Tarea pausada", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/capture")
    def task_capture(task_id):
        run_task(task_id, "MANUAL_CAPTURE")
        flash("Captura hecha (sin enviar correo). Mira el historial.", "success")
        return redirect(url_for("runs", task_id=task_id))

    @app.post("/tasks/<int:task_id>/run")
    def task_run(task_id):
        run_task(task_id, "MANUAL_TEST")
        flash("Test completo ejecutado. Mira el historial.", "success")
        return redirect(url_for("runs", task_id=task_id))

    @app.get("/smtp")
    def smtp_list():
        profiles = SmtpProfile.query.order_by(SmtpProfile.id.desc()).all()
        return render_template("smtp_list.html", profiles=profiles)

    @app.get("/smtp/new")
    def smtp_new():
        return render_template("smtp_form.html", p=None)

    @app.post("/smtp/new")
    def smtp_new_post():
        p = SmtpProfile()
        _fill_smtp_from_form(p, request.form)
        db.session.add(p)
        db.session.commit()
        flash("Perfil SMTP creado", "success")
        return redirect(url_for("smtp_list"))

    @app.get("/smtp/<int:pid>/edit")
    def smtp_edit(pid):
        p = SmtpProfile.query.get_or_404(pid)
        return render_template("smtp_form.html", p=p)

    @app.post("/smtp/<int:pid>/edit")
    def smtp_edit_post(pid):
        p = SmtpProfile.query.get_or_404(pid)
        _fill_smtp_from_form(p, request.form)
        db.session.commit()
        flash("Perfil SMTP actualizado", "success")
        return redirect(url_for("smtp_list"))

    @app.post("/smtp/<int:pid>/test")
    def smtp_test(pid):
        # envia un correo simple al propio "from_email"
        p = SmtpProfile.query.get_or_404(pid)
        tmp_task = type("Tmp", (), {})()
        tmp_task.name = "SMTP TEST"
        tmp_task.to_emails = p.from_email
        tmp_task.cc_emails = ""
        tmp_task.bcc_emails = ""
        tmp_task.subject_template = "SMTP OK {date} {time}"
        tmp_task.html_template = "<html><body><h3>SMTP OK</h3><p>Esto es una prueba.</p></body></html>"
        tmp_task.text_template = "SMTP OK"
        tmp_task.url = ""
        tmp_task.attach_file = False

        # para reutilizar mailer: le pasamos una imagen dummy inline? mas simple:
        # aqui enviamos sin imagen: hack rapido -> mandamos un correo simple directo
        try:
            import smtplib
            from email.mime.text import MIMEText
            pwd = os.getenv(p.password_env, "")
            if not pwd:
                raise RuntimeError(f"Variable {p.password_env} vacia")

            msg = MIMEText("SMTP OK", "plain", "utf-8")
            msg["From"] = p.from_email
            msg["To"] = p.from_email
            msg["Subject"] = "SMTP OK"
            enc = (p.encryption or "STARTTLS").upper()

            if enc == "SSL":
                s = smtplib.SMTP_SSL(p.host, int(p.port), timeout=30)
            else:
                s = smtplib.SMTP(p.host, int(p.port), timeout=30)
            s.ehlo()
            if enc == "STARTTLS":
                s.starttls()
                s.ehlo()
            s.login(p.username, pwd)
            s.sendmail(p.from_email, [p.from_email], msg.as_string())
            s.quit()
            flash("SMTP OK (correo enviado)", "success")
        except Exception as e:
            flash(f"SMTP ERROR: {e}", "danger")

        return redirect(url_for("smtp_list"))

    def _fill_smtp_from_form(p: SmtpProfile, f):
        p.name = f.get("name", "").strip()
        p.host = f.get("host", "").strip()
        p.port = int(f.get("port", "587"))
        p.encryption = f.get("encryption", "STARTTLS").strip().upper()
        p.username = f.get("username", "").strip()
        p.password_env = f.get("password_env", "").strip()
        p.from_email = f.get("from_email", "").strip()
        p.reply_to = (f.get("reply_to", "").strip() or None)

    def _fill_task_from_form(t: Task, f):
        t.name = f.get("name", "").strip()
        t.enabled = (f.get("enabled") == "on")
        t.timezone = f.get("timezone", "Europe/Madrid").strip()

        t.schedule_type = f.get("schedule_type", "DAILY").strip().upper()
        t.time_hhmm = (f.get("time_hhmm", "").strip() or None)
        t.weekdays = (f.get("weekdays", "").strip() or None)
        t.interval_minutes = int(f.get("interval_minutes") or 0) or None

        t.url = f.get("url", "").strip()
        t.viewport_width = int(f.get("viewport_width") or 1920)
        t.viewport_height = int(f.get("viewport_height") or 5000)
        t.full_page = (f.get("full_page") == "on")

        t.device_scale_factor = float(f.get("device_scale_factor") or 1.0)
        t.css_zoom = float(f.get("css_zoom") or 1.0)

        t.wait_mode = f.get("wait_mode", "SLEEP").strip().upper()
        t.wait_seconds = int(f.get("wait_seconds") or 5)
        t.wait_selector = (f.get("wait_selector", "").strip() or None)

        t.remove_selectors = f.get("remove_selectors", "[]").strip() or "[]"
        t.pre_js = (f.get("pre_js", "").strip() or None)

        t.image_format = f.get("image_format", "PNG").strip().upper()
        t.jpeg_quality = int(f.get("jpeg_quality") or 0) or None
        t.max_width = int(f.get("max_width") or 0) or None

        t.smtp_profile_id = int(f.get("smtp_profile_id"))

        t.to_emails = f.get("to_emails", "").strip()
        t.cc_emails = (f.get("cc_emails", "").strip() or None)
        t.bcc_emails = (f.get("bcc_emails", "").strip() or None)

        t.subject_template = f.get("subject_template", "").strip() or t.subject_template
        t.html_template = f.get("html_template", "").strip() or t.html_template
        t.text_template = (f.get("text_template", "").strip() or None)

        t.attach_inline = (f.get("attach_inline") == "on")
        t.attach_file = (f.get("attach_file") == "on")
        t.retention_days = int(f.get("retention_days") or 14)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=1234)
