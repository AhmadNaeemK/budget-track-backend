from celery import shared_task
from accounts.services import notify_friend_request_all, send_user_verification_email, \
    send_password_recovery_email


@shared_task
def send_friend_request_notifications(friend_request):
    notify_friend_request_all(friend_request)


@shared_task
def send_user_verification_email_notification(user):
    send_user_verification_email(user)


@shared_task
def send_password_recovery_email_notification(user):
    send_password_recovery_email(user)
