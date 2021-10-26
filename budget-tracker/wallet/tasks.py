from celery import shared_task
from .services import send_daily_scheduled_transactions_email_reports


@shared_task
def daily_scheduled_reports():
    send_daily_scheduled_transactions_email_reports()
