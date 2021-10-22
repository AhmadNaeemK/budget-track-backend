from .models import Transaction, TransactionCategories

import datetime
from django.conf import settings
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from .models import TransactionCategories

def update_transactions():

    def send_transaction_report(recipient_email, status, transaction):
        try:
            html = render_to_string('emails/scheduledTransactionReportTemplate.html',
                                    {
                                        'title': transaction.title,
                                        'category': TransactionCategories.choices[transaction.category][1],
                                        'amount': transaction.amount,
                                        'status': status,
                                        'remaining': transaction.cash_account.balance,
                                    }
                                    )
            send_mail(subject='Scheduled Transaction ' + status,
                      message="Scheduled Transaction has " + status,
                      html_message=html,
                      from_email=settings.SENDER_EMAIL,
                      recipient_list=[recipient_email],
                      fail_silently=False)
            print('mail sent')
        except Exception as e:
            print("Error: ", e)
            return
        return

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
                    send_transaction_report(scheduled.user.email, 'Failed', scheduled)
                    return
                cash_account.balance -= scheduled.amount
            scheduled.save()
            cash_account.save()
            send_transaction_report(scheduled.user.email, 'Succeeded', scheduled)
            print('Transaction completed')


def start():
    print('scheduler started')
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_transactions, 'interval', minutes=1)
    scheduler.start()
