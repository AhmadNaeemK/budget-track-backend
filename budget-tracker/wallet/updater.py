from .models import ScheduledTransaction, Transaction

import datetime
from django.conf import settings
import pytz

from apscheduler.schedulers.background import BackgroundScheduler


def update_transactions():
    print('Trying Update')
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    scheduled_transactions = ScheduledTransaction.objects.all()
    for scheduled in scheduled_transactions:
        if scheduled.scheduled_time <= datetime.datetime.now(tz=curr_time_zone):
            Transaction.objects.create(user=scheduled.user, title=scheduled.title, amount=scheduled.amount,
                                       category=scheduled.category, cash_account=scheduled.cash_account)
            scheduled.delete()
            print('Transaction completed')


def start():
    print('scheduler started')
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_transactions, 'interval', minutes=1)
    scheduler.start()
