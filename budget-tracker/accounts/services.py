from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_friend_request_email(friend_request):
    html_message = render_to_string('emails/friendRequestNotificationTemplate.html',
                                    {'sender': friend_request.user.username}
                                    )
    try:
        send_mail(
            subject='Friend Request Received',
            recipient_list=[friend_request.receiver.email],
            html_message=html_message,
            message='Friend Request received from ' + friend_request.user.username,
            from_email=settings.SENDER_EMAIL
        )

    except Exception as e:
        print(e)


def send_friend_request_sms(friend_request):
    message = 'Friend request received from {sender} /nFrom BudgetTracker'
    try:
        settings.TWILIO_CLIENT.messages.create(
            body=message.format(sender=friend_request.user.username),
            from_=settings.PHN_NUM,
            to=friend_request.receiver.phone_number
        )
    except Exception as e:
        print(e)

