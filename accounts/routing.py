from django.urls import path

from accounts import consumers

websocket_urlpatterns = [
    path('ws/notification/<int:user_id>', consumers.NotificationConsumer.as_asgi()),
]
