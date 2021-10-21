from .models import Transaction, TransactionCategories

import datetime
from django.conf import settings
import pytz

from apscheduler.schedulers.background import BackgroundScheduler


def update_transactions():
    print('Trying Update')
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    scheduled_transactions = Transaction.objects.filter(scheduled=True)
    for scheduled in scheduled_transactions:
        if scheduled.transaction_time <= datetime.datetime.now(tz=curr_time_zone):
            scheduled.scheduled = False
            cash_account = scheduled.cash_account
            if scheduled.category == TransactionCategories.Income.value:
                cash_account.balance += scheduled.amount
            else:
                cash_account.balance -= scheduled.amount
            scheduled.save()
            cash_account.save()
            print('Transaction completed')


def start():
    print('scheduler started')
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_transactions, 'interval', minutes=1)
    scheduler.start()
