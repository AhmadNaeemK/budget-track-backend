from celery import shared_task
from accounts.services import Notification


@shared_task
def send_friend_request_notifications(friend_request):
    Notification().notify_all(Notification.FRIEND_REQUEST, friend_request)


@shared_task
def send_user_verification_email_notification(user):
    Notification().notify_email(Notification.USER_VERIFICATION, {'user_id': user})


@shared_task
def send_password_recovery_email_notification(user):
    Notification().notify_email(Notification.PASSWORD_RECOVERY, {'user_id': user})
