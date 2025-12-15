from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

def build_scheduler(app, run_task_callable):
    sched = BackgroundScheduler(timezone=pytz.timezone(app.config["DEFAULT_TZ"]))

    def reschedule_all():
        with app.app_context():
            from models import Task
            sched.remove_all_jobs()
            tasks = Task.query.filter_by(enabled=True).all()
            for t in tasks:
                tz = pytz.timezone(t.timezone or app.config["DEFAULT_TZ"])
                if t.schedule_type == "INTERVAL" and t.interval_minutes:
                    trigger = IntervalTrigger(minutes=int(t.interval_minutes), timezone=tz)
                elif t.schedule_type == "WEEKLY" and t.time_hhmm and t.weekdays:
                    hh, mm = t.time_hhmm.split(":")
                    # weekdays "1..7" -> cron: mon,tue...
                    map_wd = { "1":"mon","2":"tue","3":"wed","4":"thu","5":"fri","6":"sat","7":"sun" }
                    days = ",".join(map_wd.get(x.strip(), "") for x in t.weekdays.split(",") if x.strip() in map_wd)
                    trigger = CronTrigger(day_of_week=days, hour=int(hh), minute=int(mm), timezone=tz)
                else:
                    # DAILY default
                    hh, mm = (t.time_hhmm or "08:00").split(":")
                    trigger = CronTrigger(hour=int(hh), minute=int(mm), timezone=tz)

                sched.add_job(
                    run_task_callable,
                    trigger=trigger,
                    kwargs={"task_id": t.id, "trigger_name": "SCHEDULED"},
                    id=f"task-{t.id}",
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True,
                )

    return sched, reschedule_all
