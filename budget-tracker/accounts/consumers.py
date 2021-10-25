import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class FriendRequestConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        if not user_id:
            # Reject the connection
            self.close()
        else:
            self.group_name = str(user_id)
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()

    def disconnect(self, close_code):
        user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = str(user_id)
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def request_notification(self, event):
        print("Sending Notification")
        print(event)
        self.send(
            text_data=json.dumps({
                'friend_request': event['friend_request']
            })
        )
