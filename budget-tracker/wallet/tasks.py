import datetime
import pytz

from celery import shared_task

from django.conf import settings

from accounts.models import EmailAuthenticatedUser as User

from .models import Transaction, TransactionCategories
from .serializers import TransactionSerializer
from .services import Notification


def get_tz_aware_current_time():
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    curr_time = datetime.datetime.now(tz=curr_time_zone)  # timezone aware current time
    return curr_time


def get_scheduled_transactions_due():
    curr_time = get_tz_aware_current_time()
    scheduled_transactions = Transaction.objects.filter(scheduled=True, transaction_time__lte=curr_time)
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
            Notification().notify_all(notification_type=Notification.SCHEDULED_TRANSACTION_COMPLETION,
                                      data={
                                          'transaction': scheduled_transaction,
                                          'status': 'Failed'
                                      }
                                      )
            raise Exception(f"Cash Account of user {scheduled_transaction.user.username} does not have enough balance ")
        cash_account.balance -= scheduled_transaction.amount
    cash_account.save()
    return True


@shared_task
def update_scheduled_transactions():
    scheduled_transactions = get_scheduled_transactions_due()
    for transaction in scheduled_transactions:
        try:
            update_account(transaction)
        except Exception as AccountBalanceLimitException:
            print(AccountBalanceLimitException)
            continue

        transaction.scheduled = False
        transaction.save()
        send_all_notification.delay(notification_type=Notification.SCHEDULED_TRANSACTION_COMPLETION,
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
                                                            transaction_time__date__lte=curr_date)[:10]
        if scheduled_transactions:
            scheduled_transactions = list(TransactionSerializer(scheduled_transactions, many=True).data)
            send_email_notification.delay(notification_type=Notification.DAILY_SCHEDULED_REPORT,
                                          data={
                                              'scheduled_transactions': scheduled_transactions,
                                              'curr_date': curr_date
                                          }
                                          )


@shared_task
def send_push_notification(notification_type, data):
    Notification().notify_push(notification_type, data)


@shared_task
def send_email_notification(notification_type, data):
    Notification().notify_email(notification_type, data)


@shared_task
def send_sms_notification(notification_type, data):
    Notification().notify_sms(notification_type, data)


@shared_task
def send_all_notification(notification_type, data):
    Notification().notify_all(notification_type, data)
