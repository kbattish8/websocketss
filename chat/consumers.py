import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "chat_group"

        #  Proper check for authenticated user
        if self.scope["user"] and not isinstance(self.scope["user"], AnonymousUser):
            self.user_id = str(self.scope["user"].id)
        else:
            self.user_id = None

        print(f" New WebSocket connection | User: {self.user_id}")

        # Join public group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Join personal private channel
        if self.user_id:
            await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)

        await self.accept()
        await self.send(json.dumps({
            "message": " Connected to WebSocket",
            "user_id": self.user_id
        }))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message = data.get("message", "")
        recipient = data.get("recipient")

        if recipient:
            # Send private message
            await self.channel_layer.group_send(
                f"user_{recipient}",
                {"type": "private_message", "message": message, "from_user": self.user_id}
            )
        else:
            # Send group message
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "group_message", "message": message, "from_user": self.user_id}
            )

    async def group_message(self, event):
        await self.send(json.dumps({
            "type": "group",
            "message": event["message"],
            "from_user": event["from_user"]
        }))

    async def private_message(self, event):
        await self.send(json.dumps({
            "type": "private",
            "message": event["message"],
            "from_user": event["from_user"]
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.user_id:
            await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)
