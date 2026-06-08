import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def start_scheduler() -> BackgroundScheduler:
    from autonomous import publish_pending_posts, plan_and_schedule_week, generate_weekly_report

    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

    # Publica posts pendentes a cada minuto
    scheduler.add_job(publish_pending_posts, "interval", minutes=1, id="publish")

    # Planejamento semanal: toda segunda-feira às 8h
    scheduler.add_job(
        lambda: plan_and_schedule_week(),
        "cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly_plan",
    )

    # Relatório semanal: todo domingo às 18h
    scheduler.add_job(
        generate_weekly_report,
        "cron",
        day_of_week="sun",
        hour=18,
        minute=0,
        id="weekly_report",
    )

    scheduler.start()
    logger.info("Scheduler iniciado: publicação a cada minuto, planejamento toda segunda às 8h.")
    return scheduler
