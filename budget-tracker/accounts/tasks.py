from celery import shared_task
from .services import notify_all

@shared_task
def send_friend_request_notifications(friend_request):
    notify_all(friend_request)