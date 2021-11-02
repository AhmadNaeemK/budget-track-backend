from celery import shared_task
from .services import notify_friend_request_all, send_user_verification_email

@shared_task
def send_friend_request_notifications(friend_request):
    notify_friend_request_all(friend_request)

@shared_task
def send_user_verification_email_notification(user):
    send_user_verification_email(user)
