from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Sum

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import pytz, datetime

from .models import TransactionCategories, Transaction
from accounts.models import EmailAuthenticatedUser as User

from .serializers import TransactionSerializer

SPLIT_INCLUDE_NOTIFICATION = 0
SPLIT_PAYMENT_NOTIFICATION = 1
SCHEDULED_TRANSACTION_COMPLETION = 2


def get_tz_aware_current_time():
    curr_time_zone = pytz.timezone(settings.TIME_ZONE)
    curr_time = datetime.datetime.now(tz=curr_time_zone)  # timezone aware current time
    return curr_time


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


class EmailNotification:
    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        self._send_email_notification(**notification(**data))

    def _select_notification(self, notification_type):
        if notification_type == SPLIT_INCLUDE_NOTIFICATION:
            return self._for_split_include_notification
        elif notification_type == SPLIT_PAYMENT_NOTIFICATION:
            return self._for_split_payment_notification
        elif notification_type == SCHEDULED_TRANSACTION_COMPLETION:
            return self._for_scheduled_transaction_report()

    def _send_email_notification(self, template, context, subject, message, recipient_list):
        html_message = render_to_string(template_name=template,
                                        context=context
                                        )
        send_mail(subject=subject,
                  message=message,
                  html_message=html_message,
                  recipient_list=recipient_list,
                  from_email=settings.SENDER_EMAIL
                  )

    def _for_split_include_notification(self, split):
        context = {
            'title': split.title,
            'category': TransactionCategories.choices[split.category][1],
            'total_amount': split.total_amount,
            'paying_friend': split.paying_friend.username
        }
        title = f"{split.title} paid by {split.paying_friend.username}"
        return {'template': 'emails/splitIncludeNotificationTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': split.all_friends_involved.all()
                }

    def _for_split_payment_notification(self, split, user, payment):
        split_payment = split.total_amount // len(split.all_friends_involved.all())
        paid_amount = Transaction.objects.filter(user=user.id, split_expense=split).aggregate(Sum('amount'))[
            'amount__sum']
        context = {
            'title': split.title,
            'category': TransactionCategories.choices[split.category][1],
            'total_split': split_payment,
            'payment': payment,
            'rem_payment': (
                    split_payment - paid_amount - payment
            ),
        }
        title = f"Payment for {split.title} paid by {user.username}"
        return {'template': 'emails/splitIncludeNotificationTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': [split.paying_friend.email]
                }

    def _for_scheduled_transaction_report(self, transaction, status):
        context = {
            'title': transaction.title,
            'category': TransactionCategories.choices[transaction.category][1],
            'amount': transaction.amount,
            'status': status,
            'remaining': transaction.cash_account.balance,
        }
        title = f'Scheduled Transaction has {status}'
        return {'template': 'emails/scheduledTransactionReportTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': [transaction.user.email]
                }


class SMSNotification:
    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        notification(**data)

    def _select_notification(self, notification_type):
        if notification_type == SPLIT_INCLUDE_NOTIFICATION:
            return self._for_split_include_notification
        elif notification_type == SPLIT_PAYMENT_NOTIFICATION:
            return self._for_split_payment_notification
        elif notification_type == SCHEDULED_TRANSACTION_COMPLETION:
            return self._for_scheduled_transaction_report()

    def _send_sms_notification(self, message, recipient_phone):
        try:
            message += '\nFrom BudgetTracker'
            settings.TWILIO_CLIENT.messages.create(
                body=message,
                from_=settings.PHN_NUM,
                to=recipient_phone
            )
        except Exception as e:
            print(e)

    def _for_split_include_notification(self, split):
        message = f'You have been added to a split expense for {split.title} by {split.creator.username}.' \
                  f'\nAmount Paid by {split.paying_friend.username}: {split.total_amount}'
        for friend in split.all_friends_involved.all():
            self._send_sms_notification(
                message=message,
                recipient_phone=friend.phone_number
            )

    def _for_split_payment_notification(self, split, user, payment):

        message = f'Payment amount {payment} for {split.title} made by {user.username}, added to your cash account'
        self._send_sms_notification(
            message=message,
            recipient_phone=split.paying_friend.phone_number
        )

    def _for_scheduled_transaction_report(self, transaction, status):
        message = f'Scheduled Transaction for {transaction.title} has {status}\nTransaction Amount: {transaction.amount}'
        self._send_sms_notification(
            message=message,
            recipient_phone=transaction.user.phone_number
        )


class PushNotification:
    def notify(self, data, notification_type):
        print(data)
        notification = self._select_notification(notification_type)
        notification(**data)

    def _select_notification(self, notification_type):
        if notification_type == SPLIT_INCLUDE_NOTIFICATION:
            return self._for_split_include_notification
        elif notification_type == SPLIT_PAYMENT_NOTIFICATION:
            return self._for_split_payment_notification
        elif notification_type == SCHEDULED_TRANSACTION_COMPLETION:
            return self._for_scheduled_transaction_report()

    def _send_push_notification(self, message, group_name):
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

    def _for_split_include_notification(self, split):
        message = f'You have been added to a split expense for {split.title} by {split.creator.username}.'
        for friend in split.all_friends_involved.all():
            self._send_push_notification(
                message=message,
                group_name=f'notification_{friend.id}'
            )

    def _for_split_payment_notification(self, split, user, payment):

        message = f'Payment amount {payment} for split "{split.title}" made by {user.username}, added to your cash account'
        self._send_push_notification(
            message=message,
            group_name=split.paying_friend.id
        )

    def _for_scheduled_transaction_report(self, transaction, status):
        message = f'Scheduled Transaction for {transaction.title} has {status}.\nTransaction Amount: {transaction.amount}'
        self._send_push_notification(
            message=message,
            group_name=f'notification_{transaction.user.id}'
        )