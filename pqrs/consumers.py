from core.models import ChatRooms, MessageByRooms
from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync

class WSconsumer(WebsocketConsumer):
    groupObject = ''
    def connect(self):
        groupObject = ChatRooms.objects.get(code_room=self.scope['url_route']['kwargs']['code_room'])
        self.room_name = groupObject.name_room
        self.room_group_name = 'room_%s' % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        # Join room group
        self.accept()
        messages = MessageByRooms.objects.all().filter(
            associate_room=ChatRooms.objects.get(code_room=self.scope['url_route']['kwargs']['code_room'])
        )
        for message in messages:
            res={
                'type': 'send_message',
                'user':message.user,
                'message': message.message_value,
            }
            self.send(text_data=json.dumps({
                "payload": res,
            }))

    def disconnect(self, close_code):
        print("Disconnected")
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """
        Receive message from WebSocket.
        Get the event and send the appropriate event
        """
        response = json.loads(text_data)
        user = response.get("user", None)
        message = response.get("message", None)
        groupObject = ChatRooms.objects.get(code_room=self.scope['url_route']['kwargs']['code_room'])
        new_message = MessageByRooms(
            message_value=message,
            user=user,
            associate_room=groupObject
        )
        new_message.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
            'type': 'send_message',
            'user':user,
            'message': message,
            })


    def send_message(self, res):
        """ Receive message from room group """
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "payload": res,
        }))