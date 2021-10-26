from .models import Transaction, TransactionCategories

from apscheduler.schedulers.background import BackgroundScheduler

from .models import TransactionCategories
from .services import send_scheduled_transaction_report_mail, send_scheduled_transaction_report_sms
from .services import get_tz_aware_current_time


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


def update_scheduled_transactions():
    scheduled_transactions = get_scheduled_transactions_due()
    for transaction in scheduled_transactions:
        transaction.scheduled = not update_account(transaction)
        if not transaction.scheduled:
            transaction.save()
            send_scheduled_transaction_report_mail(transaction, 'Succeeded')
            send_scheduled_transaction_report_sms(transaction, 'Succeeded')
            print('Transaction completed')


def start():
    print('scheduler started')
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_scheduled_transactions, 'interval', minutes=1)
    scheduler.start()
