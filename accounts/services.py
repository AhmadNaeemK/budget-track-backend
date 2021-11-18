from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework_simplejwt.tokens import RefreshToken

from twilio.base.exceptions import TwilioRestException

from .models import EmailAuthenticatedUser


class EmailNotification:
    budget_tracker_link = settings.FRONTEND_URL

    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        self._send_email_notification(notification(data))

    def _select_notification(self, notification_type):
        if notification_type == Notification.FRIEND_REQUEST:
            return self._for_friend_request
        elif notification_type == Notification.USER_VERIFICATION:
            return self._for_user_verification
        elif notification_type == Notification.PASSWORD_RECOVERY:
            return self._for_password_recovery

    def _send_email_notification(self, email_data):
        html_message = render_to_string(template_name=email_data["template"],
                                        context=email_data["context"]
                                        )
        send_mail(subject=email_data["subject"],
                  message=email_data["message"],
                  html_message=html_message,
                  recipient_list=email_data["recipient_list"],
                  from_email=settings.SENDER_EMAIL
                  )

    def _for_friend_request(self, data):
        context = {'sender': data['user']['username'],
                   'button_text': 'Verify',
                   'button_link': settings.FRONTEND_URL
                   }
        return {'template': 'emails/friendRequestNotificationTemplate.html',
                'context': context,
                'subject': 'Friend Request Received',
                'message': 'Friend Request',
                'recipient_list': [data["receiver"]["email"]]
                }

    def _for_user_verification(self, data):
        user = EmailAuthenticatedUser.objects.get(pk=data['user_id'])
        token = RefreshToken.for_user(user).access_token
        context = {
            'button_text': 'Verify',
            'button_link': f'{settings.FRONTEND_URL}/user/verify?token={token}'
        }
        return {'template': 'emails/userVerificationEmailTemplate.html',
                'context': context,
                'subject': 'BudgetTracker account verification',
                'message': 'BudgetTracker Account verification',
                'recipient_list': [user.email]
                }

    def _for_password_recovery(self, data):
        user = EmailAuthenticatedUser.objects.get(pk=data['user_id'])
        context = {
            'button_text': 'Verify',
            'button_link': f'{settings.FRONTEND_URL}/'
                           f'recover/password?token={RefreshToken.for_user(user).access_token}'
        }
        return {'template': 'emails/passwordRecoveryMailTemplate.html',
                'context': context,
                'subject': 'BudgetTracker Recover Password',
                'message': 'BudgetTracker Recover Password',
                'recipient_list': [user.email]
                }


class SMSNotification:
    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        notification(data)

    def _select_notification(self, notification_type):
        if notification_type == Notification.FRIEND_REQUEST:
            return self._for_friend_request

    def _send_sms_notification(self, message, recipient_phone):
        message += '\nFrom BudgetTracker'
        try:
            settings.TWILIO_CLIENT.messages.create(
                body=message,
                from_=settings.PHN_NUM,
                to=recipient_phone
            )
        except TwilioRestException as twilio_exception:
            print(twilio_exception)

    def _for_friend_request(self, data):
        message = f'Friend request received from {data["user"]["username"]}'
        self._send_sms_notification(
            message=message,
            recipient_phone=data["receiver"]["phone_number"]
        )


class PushNotification:
    def notify(self, data, notification_type):
        notification = self._select_notification(notification_type)
        notification(data)

    def _select_notification(self, notification_type):
        if notification_type == Notification.FRIEND_REQUEST:
            return self._for_friend_request

    def _send_push_notification(self, message, group_name):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "notification": message,
            },
        )

    def _for_friend_request(self, data):
        message = f'Friend request received from {data["user"]["username"]}'
        self._send_push_notification(
            message=message,
            group_name=f'notification_{data["receiver"]["id"]}'
        )


class Notification:
    FRIEND_REQUEST = 0
    USER_VERIFICATION = 1
    PASSWORD_RECOVERY = 2

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
