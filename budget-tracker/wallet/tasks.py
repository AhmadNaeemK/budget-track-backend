from celery import shared_task

from .models import Transaction, TransactionCategories

from .services import send_daily_scheduled_transactions_email_reports, get_tz_aware_current_time
from .services import send_scheduled_transaction_report_mail, send_scheduled_transaction_report_sms
from .services import PushNotification, EmailNotification


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
            print('Account Does not has enough balance')
            send_scheduled_transaction_report_mail(scheduled_transaction, 'Failed')
            send_scheduled_transaction_report_sms(scheduled_transaction, 'Failed')
            return False
        cash_account.balance -= scheduled_transaction.amount
    cash_account.save()
    return True


@shared_task
def update_scheduled_transactions():
    scheduled_transactions = get_scheduled_transactions_due()
    for transaction in scheduled_transactions:
        transaction.scheduled = not update_account(transaction)
        if not transaction.scheduled:
            transaction.save()
            # send_scheduled_transaction_report_mail(transaction, 'Succeeded')
            # send_scheduled_transaction_report_sms(transaction, 'Succeeded')
            # PushNotification().notify(
            #     notification_type=2,
            #     data={
            #         'transaction': transaction,
            #         'status': 'Succeeded',
            #     }
            # )
            EmailNotification().notify(notification_type=2,
                                       data={
                                           'transaction': transaction,
                                           'status': 'Succeeded'
                                       })
            print('Transaction completed')


@shared_task
def daily_scheduled_reports():
    send_daily_scheduled_transactions_email_reports()
