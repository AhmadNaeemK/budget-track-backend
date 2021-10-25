from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/friendRequestsNotification/<int:user_id>', consumers.FriendRequestConsumer.as_asgi()),
]