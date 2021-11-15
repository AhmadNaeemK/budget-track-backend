""" Tasks module for Celery Tasks """

import datetime

import pytz
from celery import shared_task
from django.conf import settings

from accounts.models import EmailAuthenticatedUser as User
from wallet.models import Transaction, TransactionCategories
from wallet.serializers import TransactionSerializer
from wallet.services import Notification
from wallet.exceptions import AccountBalanceLimitException


def get_tz_aware_current_time():
    """
    returns timezone aware time
    """
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    curr_time = datetime.datetime.now(tz=curr_time_zone)
    return curr_time


def get_scheduled_transactions_due():
    """
    returns scheduled transactions from database
    """
    curr_time = get_tz_aware_current_time()
    scheduled_transactions = Transaction.objects.filter(scheduled=True,
                                                        transaction_time__lte=
                                                        curr_time)
    return scheduled_transactions


def update_account(scheduled_transaction):
    """
    returns: True when account updated successfully, else False
    """
    cash_account = scheduled_transaction.cash_account
    if scheduled_transaction.category == TransactionCategories.Income.value:
        cash_account.balance += scheduled_transaction.amount
    else:
        if cash_account.balance < scheduled_transaction.amount:
            Notification().notify_all(notification_type=
                                      Notification.SCHEDULED_TRANSACTION_COMPLETION,
                                      data={
                                          'transaction': scheduled_transaction,
                                          'status': 'Failed'
                                      }
                                      )
            raise AccountBalanceLimitException(scheduled_transaction.user.username)
        cash_account.balance -= scheduled_transaction.amount
    cash_account.save()
    return True


@shared_task
def update_scheduled_transactions():
    """
    celery task to complete the scheduled transactions
    """
    scheduled_transactions = get_scheduled_transactions_due()
    for transaction in scheduled_transactions:
        try:
            update_account(transaction)
        except AccountBalanceLimitException:
            print(AccountBalanceLimitException)
            continue

        transaction.scheduled = False
        transaction.save()
        send_all_notification.delay(
            notification_type=Notification.SCHEDULED_TRANSACTION_COMPLETION,
            data={
                'transaction': TransactionSerializer(transaction).data,
                'status': 'Succeeded'
            }
        )
        print("Transaction Completed")


@shared_task
def send_daily_scheduled_transactions_email_reports():
    """
        send email report for transactions due for the day
    """
    curr_time = get_tz_aware_current_time()
    curr_date = curr_time.date()
    users = User.objects.all()
    for user in users:
        scheduled_transactions = Transaction.objects.filter(user=user,
                                                            scheduled=True,
                                                            transaction_time__date__lte=curr_date
                                                            )[:10]
        if scheduled_transactions:
            scheduled_transactions = list(
                TransactionSerializer(scheduled_transactions, many=True
                                      ).data)
            send_email_notification.delay(
                notification_type=Notification.DAILY_SCHEDULED_REPORT,
                data={
                    'scheduled_transactions': scheduled_transactions,
                    'curr_date': curr_date
                }
            )


@shared_task
def send_push_notification(notification_type, data):
    """
    celery task to send push notifications
    """
    Notification().notify_push(notification_type, data)


@shared_task
def send_email_notification(notification_type, data):
    """
    celery task to send email notifications
    """
    Notification().notify_email(notification_type, data)


@shared_task
def send_sms_notification(notification_type, data):
    """
        celery task to send sms notifications
        """
    Notification().notify_sms(notification_type, data)


@shared_task
def send_all_notification(notification_type, data):
    """
        celery task to send email, sms and push
    """
    Notification().notify_all(notification_type, data)
