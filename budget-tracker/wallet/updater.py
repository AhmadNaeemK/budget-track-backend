from .models import Transaction, TransactionCategories

import datetime
from django.conf import settings
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from .models import TransactionCategories
from .services import send_scheduled_transaction_report_mail, send_scheduled_transaction_report_sms


def update_transactions():
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    scheduled_transactions = Transaction.objects.filter(scheduled=True)
    for scheduled in scheduled_transactions:
        if scheduled.transaction_time <= datetime.datetime.now(tz=curr_time_zone):
            scheduled.scheduled = False
            cash_account = scheduled.cash_account
            if scheduled.category == TransactionCategories.Income.value:
                cash_account.balance += scheduled.amount
            else:
                if cash_account.balance < scheduled.amount:
                    print('Account Does not has enough balance')
                    send_scheduled_transaction_report_mail(scheduled, 'Failed')
                    send_scheduled_transaction_report_sms(scheduled, 'Failed')
                    return
                cash_account.balance -= scheduled.amount
            scheduled.save()
            cash_account.save()
            send_scheduled_transaction_report_mail(scheduled, 'Succeeded')
            send_scheduled_transaction_report_sms(scheduled, 'Succeeded')
            print('Transaction completed')


def start():
    print('scheduler started')
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_transactions, 'interval', minutes=1)
    scheduler.start()
