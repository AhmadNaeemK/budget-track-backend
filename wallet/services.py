from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from twilio.base.exceptions import TwilioRestException


class EmailNotification:

    budget_tracker_link = settings.FRONTEND_URL

    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        self._send_email_notification(**notification(data))

    def _select_notification(self, notification_type):
        if notification_type == Notification.SPLIT_INCLUDE_NOTIFICATION:
            return self._for_split_include_notification
        elif notification_type == Notification.SPLIT_PAYMENT_NOTIFICATION:
            return self._for_split_payment_notification
        elif notification_type == Notification.SCHEDULED_TRANSACTION_COMPLETION:
            return self._for_scheduled_transaction_report
        elif notification_type == Notification.DAILY_SCHEDULED_REPORT:
            return self._for_daily_scheduled_report

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

    def _for_split_include_notification(self, data):
        context = {
            'title': data["split"]["title"],
            'category': data["split"]["category"][1],
            'total_amount': data["split"]["total_amount"],
            'paying_friend': data["split"]["paying_friend"]["username"],
            'button_text': 'View More',
            'button_link': self.budget_tracker_link
        }
        title = f'{data["split"]["title"]} paid by {data["split"]["paying_friend"]["username"]}'
        return {'template': 'emails/splitIncludeNotificationTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': [friend["email"] for friend in data["split"]["all_friends_involved"]]
                }

    def _for_split_payment_notification(self, data):
        context = {
            'title': data["split"]["title"],
            'category': data["split"]["category"][1],
            'total_split': data["split_payment"],
            'payment': data["payment"],
            'rem_payment': (
                    data["split_payment"] - data["paid_amount"] - data["payment"]
            ),
            'button_text': 'View More',
            'button_link': self.budget_tracker_link
        }
        title = f'Payment for {data["split"]["title"]} paid by {data["user"]["username"]}'
        return {'template': 'emails/splitPaymentReportTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': [data["split"]["paying_friend"]["email"]]
                }

    def _for_scheduled_transaction_report(self, data):
        context = {
            'title': data["transaction"]["title"],
            'category': data["transaction"]["category"][1],
            'amount': data["transaction"]["amount"],
            'status': data["status"],
            'remaining': data["transaction"]["cash_account"]["balance"],
            'button_text': 'View More',
            'button_link': self.budget_tracker_link
        }
        title = f'Scheduled Transaction has {data["status"]}'
        return {'template': 'emails/scheduledTransactionReportTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': [data["transaction"]["user"]["email"]]
                }

    def _for_daily_scheduled_report(self, data):
        context = {**data, 'button_text': 'View More', 'button_link': self.budget_tracker_link}
        title = f"Transactions Scheduled for Today {data['curr_date']}"
        return {'template': 'emails/scheduledTransactionsTodayTemplate.html',
                'context': context,
                'subject': title,
                'message': title,
                'recipient_list': [data["scheduled_transactions"][0]["user"]["email"]]
                }


class SMSNotification:
    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        notification(data)

    def _select_notification(self, notification_type):
        if notification_type == Notification.SPLIT_INCLUDE_NOTIFICATION:
            return self._for_split_include_notification
        elif notification_type == Notification.SPLIT_PAYMENT_NOTIFICATION:
            return self._for_split_payment_notification
        elif notification_type == Notification.SCHEDULED_TRANSACTION_COMPLETION:
            return self._for_scheduled_transaction_report

    def _send_sms_notification(self, message, recipient_phone):
        message += '\nFrom BudgetTracker'
        try:
            settings.TWILIO_CLIENT.messages.create(
                body=message,
                from_=settings.PHN_NUM,
                to=recipient_phone
            )
        except TwilioRestException as e:
            print(e)

    def _for_split_include_notification(self, data):
        message = f'You have been added to a split expense ' \
                  f'for {data["split"]["title"]} by {data["split"]["creator"]["username"]}.' \
                  f'\nAmount Paid by {data["split"]["paying_friend"]["username"]}: {data["split"]["total_amount"]}'
        for friend in data["split"]["all_friends_involved"]:
            self._send_sms_notification(
                message=message,
                recipient_phone=friend["phone_number"]
            )

    def _for_split_payment_notification(self, data):

        message = f'Payment amount {data["payment"]} for {data["split"]["title"]} made by {data["user"]["username"]}' \
                  f', added to your cash account'
        self._send_sms_notification(
            message=message,
            recipient_phone=data["split"]["paying_friend"]["phone_number"]
        )

    def _for_scheduled_transaction_report(self, data):
        message = f'Scheduled Transaction for {data["transaction"]["title"]} has {data["status"]}' \
                  f'\nTransaction Amount: {data["transaction"]["amount"]}'
        self._send_sms_notification(
            message=message,
            recipient_phone=data["transaction"]["user"]["phone_number"]
        )


class PushNotification:
    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        notification(data)

    def _select_notification(self, notification_type):
        if notification_type == Notification.SPLIT_INCLUDE_NOTIFICATION:
            return self._for_split_include_notification
        elif notification_type == Notification.SPLIT_PAYMENT_NOTIFICATION:
            return self._for_split_payment_notification
        elif notification_type == Notification.SCHEDULED_TRANSACTION_COMPLETION:
            return self._for_scheduled_transaction_report

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

    def _for_split_include_notification(self, data):
        message = f'You have been added to a split expense for {data["split"]["title"]} by ' \
                  f'{data["split"]["creator"]["username"]}.'
        for friend in data.get("split")["all_friends_involved"]:
            self._send_push_notification(
                message=message,
                group_name=f'notification_{friend["id"]}'
            )

    def _for_split_payment_notification(self, data):

        message = f'Payment amount {data["payment"]} for split "{data["split"]["title"]}" made ' \
                  f'by {data["user"]["username"]}, added to your cash account'
        self._send_push_notification(
            message=message,
            group_name=f'notification_{data["split"]["paying_friend"]["id"]}'
        )

    def _for_scheduled_transaction_report(self, data):
        message = f'Scheduled Transaction for {data["transaction"]["title"]} has {data["status"]}.' \
                  f'\nTransaction Amount: {data["transaction"]["amount"]}'
        self._send_push_notification(
            message=message,
            group_name=f'notification_{data["transaction"]["user"]["id"]}'
        )


class Notification:
    SPLIT_INCLUDE_NOTIFICATION = 0
    SPLIT_PAYMENT_NOTIFICATION = 1
    SCHEDULED_TRANSACTION_COMPLETION = 2
    DAILY_SCHEDULED_REPORT = 3

    def __init__(self):
        self._email_service = EmailNotification()
        self._sms_service = SMSNotification()
        self._push_notification_service = PushNotification()

    def notify_all(self, notification_type, data):
        self._email_service.notify(data, notification_type)
        self._push_notification_service.notify(data, notification_type)
        self._sms_service.notify(data, notification_type)

    def notify_email(self, notification_type, data):
        self._email_service.notify(data, notification_type)

    def notify_sms(self, notification_type, data):
        self._sms_service.notify(data, notification_type)

    def notify_push(self, notification_type, data):
        self._push_notification_service.notify(data, notification_type)
