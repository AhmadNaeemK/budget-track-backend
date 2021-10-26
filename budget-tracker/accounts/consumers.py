import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        if not user_id:
            # Reject the connection
            self.close()
        else:
            self.group_name = 'notification_%s' % str(user_id)
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()

    def disconnect(self, close_code):
        user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = 'notification_%s' % str(user_id)
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def send_notification(self, event):
        self.send(
            text_data=json.dumps({
                'notification': event['notification']
            })
        )
