import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_tracker.settings')

app = Celery('budget_tracker')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send_daily_scheduled_reports': {
        'task': 'wallet.tasks.send_daily_scheduled_transactions_email_reports',
        'schedule': crontab(hour=0, minute=0),
    },
    'update_scheduled_transactions': {
        'task': 'wallet.tasks.update_scheduled_transactions',
        'schedule': crontab(minute='*/1')
    }
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
