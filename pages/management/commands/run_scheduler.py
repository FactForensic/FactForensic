import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)


def fetch_news_job():
    """Function to be ran by the scheduler."""
    print(f"[{timezone.now()}] Starting scheduled news fetch...")
    try:
        call_command("fetch")
        print(f"[{timezone.now()}] Scheduled news fetch completed successfully.")
    except Exception as e:
        print(f"[{timezone.now()}] Error during scheduled news fetch: {e}")


# The `close_old_connections` decorator ensures that database connections,
# that may have become stale or closed are replaced.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries from the database every week.
    It helps to keep the database size manageable.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler to fetch news every 12 hours."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # 1. Add news fetching job
        scheduler.add_job(
            fetch_news_job,
            trigger=IntervalTrigger(hours=12),
            id="fetch_news_job",
            max_instances=1,
            replace_existing=True,
            next_run_time=timezone.now(),  # RUN IMMEDIATELY on start
        )
        logger.info("Added job 'fetch_news_job'.")

        # 2. Add maintenance job (cleanup old execution logs)
        scheduler.add_job(
            delete_old_job_executions,
            trigger=IntervalTrigger(days=7),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added weekly job 'delete_old_job_executions'.")

        try:
            logger.info("Starting scheduler...")
            print(f"[{timezone.now()}] News Scheduler Started (Interval: 12h)")
            print("Press Ctrl+C to exit.")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
