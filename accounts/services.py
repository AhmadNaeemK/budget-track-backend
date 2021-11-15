import jwt
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import EmailAuthenticatedUser

from rest_framework_simplejwt.tokens import RefreshToken


def send_friend_request_email(friend_request):
    html_message = render_to_string('emails/friendRequestNotificationTemplate.html',
                                    {'sender': friend_request['user']['username'],
                                     'button_text': 'Verify',
                                     'button_link': settings.FRONTEND_URL
                                     }
                                    )
    try:
        send_mail(
            subject='Friend Request Received',
            recipient_list=[friend_request['receiver']['email']],
            html_message=html_message,
            message='Friend Request received from ' + friend_request['user']['username'],
            from_email=settings.SENDER_EMAIL
        )

    except Exception as e:
        print(e)


def send_friend_request_sms(friend_request):
    message = 'Friend request received from {sender} \nFrom BudgetTracker'
    try:
        settings.TWILIO_CLIENT.messages.create(
            body=message.format(sender=friend_request['user']['username']),
            from_=settings.PHN_NUM,
            to=friend_request['receiver']['phone_number']
        )
    except Exception as e:
        print(e)


def send_friend_request_push_notification(friend_request):
    channel_layer = get_channel_layer()
    group_name = 'notification_%s' % str(friend_request['receiver']['id'])
    try:
        message = 'Friend request received from %s' % friend_request['user']['username']
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "notification": message,
            },
        )
    except Exception as e:
        print(e)


def send_user_verification_email(user_id):
    user = EmailAuthenticatedUser.objects.get(pk=user_id)
    token = RefreshToken.for_user(user).access_token
    context = {
        'button_text': 'Verify',
        'button_link': f'{settings.FRONTEND_URL}/user/verify?token={token}'
    }
    html_message = render_to_string('emails/userVerificationEmailTemplate.html',
                                    context=context
                                    )
    try:
        send_mail(
            subject='BudgetTracker Email Verification',
            recipient_list=[user.email],
            html_message=html_message,
            message='Verify your BudgetTracker account',
            from_email=settings.SENDER_EMAIL
        )

    except Exception as e:
        print(e)


def send_password_recovery_email(user_id):
    user = EmailAuthenticatedUser.objects.get(pk=user_id)
    context = {
        'button_text': 'Verify',
        'button_link': f'{settings.FRONTEND_URL}/recover/password?token={str(RefreshToken.for_user(user).access_token)}'
    }
    html_message = render_to_string('emails/passwordRecoveryMailTemplate.html',
                                    context=context
                                    )
    try:
        send_mail(
            subject='BudgetTracker Password Recovery',
            recipient_list=[user.email],
            html_message=html_message,
            message='Recover Password',
            from_email=settings.SENDER_EMAIL
        )

    except Exception as e:
        print(e)


def notify_friend_request_all(friend_request):
    send_friend_request_push_notification(friend_request)
    send_friend_request_sms(friend_request)
    send_friend_request_email(friend_request)
