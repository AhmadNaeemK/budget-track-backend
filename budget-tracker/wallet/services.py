from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import TransactionCategories, Transaction
from accounts.models import EmailAuthenticatedUser as User

from.serializers import TransactionSerializer

import datetime
import pytz


def get_tz_aware_current_time():
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    curr_time = datetime.datetime.now(tz=curr_time_zone)  # timezone aware current time
    return curr_time


def send_scheduled_transaction_report_mail(transaction, status):
    html = render_to_string('emails/scheduledTransactionReportTemplate.html',
                            {
                                'title': transaction.title,
                                'category': TransactionCategories.choices[transaction.category][1],
                                'amount': transaction.amount,
                                'status': status,
                                'remaining': transaction.cash_account.balance,
                            }
                            )
    send_mail(
        subject='Scheduled Transaction ' + status,
        message="Scheduled Transaction has " + status,
        html_message=html,
        recipient_list=[transaction.user.email],
        from_email=settings.SENDER_EMAIL
    )


def send_scheduled_transaction_report_sms(transaction, status):
    message = 'Scheduled Transaction for {title} has {status}' + \
              '\nTransaction Amount: {amount}' \
              '\nFrom BudgetTracker'

    try:
        settings.TWILIO_CLIENT.messages.create(
            body=message.format(title=transaction.title,
                                status=status,
                                amount=transaction.amount),
            from_=settings.PHN_NUM,
            to=transaction.user.phone_number
        )
    except Exception as e:
        print(e)


def send_split_expense_payment_report_mail(split, user, split_payment, paid_amount, payment):
    html_message = render_to_string('emails/splitPaymentReportTemplate.html',
                                    {
                                        'title': split.title,
                                        'category': TransactionCategories.choices[split.category][1],
                                        'total_split': split_payment,
                                        'payment': payment,
                                        'rem_payment': (
                                                split_payment - paid_amount - payment
                                        ),
                                    }
                                    )

    title = "Payment for {split_title} paid by {user}".format(split_title=split.title,
                                                              user=user.username)
    send_mail(subject=title,
              message=title,
              html_message=html_message,
              recipient_list=[split.paying_friend.email],
              from_email=settings.SENDER_EMAIL
              )


def send_split_expense_payment_report_sms(split, user, payment):
    message = 'Payment amount {payment} for {title} made by {user}, added to your cash account' \
              '\nFrom BudgetTracker'
    try:
        settings.TWILIO_CLIENT.messages.create(
            body=message.format(title=split.title,
                                user=user.username,
                                payment=payment),
            from_=settings.PHN_NUM,
            to=split.paying_friend.phone_number
        )
    except Exception as e:
        print(e)


def send_split_expense_payment_push_notification(split, user, payment):
    message = f'Payment amount {payment} for {split.title} made by {user.username}, added to your cash account'
    group_name = 'notification_%s' % str(split.paying_friend.id)
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "notification": message,
            },
        )
    except Exception as e:
        print(e)


def send_split_include_notification_mail(split):
    html_message = render_to_string('emails/splitIncludeNotificationTemplate.html',
                                    {
                                        'title': split.title,
                                        'category': TransactionCategories.choices[split.category][1],
                                        'total_amount': split.total_amount,
                                        'paying_friend': split.paying_friend.username
                                    }
                                    )
    title = "{split_title} paid by {split_creator}".format(split_title=split.title,
                                                           split_creator=split.creator.username)
    send_mail(subject=title,
              message=title,
              html_message=html_message,
              recipient_list=split.all_friends_involved.all(),
              from_email=settings.SENDER_EMAIL
              )


def send_split_include_notification_sms(split):
    message = 'You have been added to a split expense for {title} by {creator}.' \
              '\nAmount Paid by {paying_friend}: {total_amount}' \
              '\nFrom BudgetTracker'
    for friend in split.all_friends_involved.all():
        try:
            settings.TWILIO_CLIENT.messages.create(
                body=message.format(title=split.title,
                                    creator=split.creator.username,
                                    paying_friend=split.paying_friend.username,
                                    total_amount=split.total_amount),
                from_=settings.PHN_NUM,
                to=friend.phone_number
            )
        except Exception as e:
            print(e)


def send_split_include_push_notification(split):
    channel_layer = get_channel_layer()
    for friend in split.all_friends_involved.all():
        group_name = 'notification_%s' % str(friend.id)
        try:
            message = f'You have been added to split {split.title} by {split.creator.username}'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",
                    "notification": message,
                },
            )
        except Exception as e:
            print(e)


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
            scheduled_transactions = TransactionSerializer(scheduled_transactions, many=True)
            html_message = render_to_string('emails/scheduledTransactionsTodayTemplate.html',
                                            {
                                                'scheduled_transactions': scheduled_transactions.data
                                            }
                                            )
            title = f"Transactions Scheduled for Today {curr_date}"
            send_mail(subject=title,
                      message=title,
                      html_message=html_message,
                      recipient_list=[user.email],
                      from_email=settings.SENDER_EMAIL
                      )
