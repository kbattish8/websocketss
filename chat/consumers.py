import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Main group name for group chat
        self.group_name = "chat_group"

        # Get user_id (prefer authenticated user, else from query params)
        if self.scope["user"].is_authenticated:
            self.user_id = str(self.scope["user"].id)
        else:
            params = parse_qs(self.scope["query_string"].decode())
            self.user_id = params.get("user_id", [None])[0]

        print("🚀 New WebSocket connection established")
        print(f"👤 User ID: {self.user_id} joined")

        # Join public group chat
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Join private group for direct messages
        if self.user_id:
            await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)

        # Accept connection
        await self.accept()

        # Send confirmation to client
        await self.send(text_data=json.dumps({
            "message": "✅ Connected to WebSocket",
            "user_id": self.user_id
        }))

    async def receive(self, text_data):
        print(f"\n📩 Raw text from client: {text_data}")

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON received")
            return

        message = data.get("message", "")
        recipient = data.get("recipient")  # User ID for private chat

        if recipient:
            # Send private message to specific user
            await self.channel_layer.group_send(
                f"user_{recipient}",
                {
                    "type": "private_message",
                    "message": message,
                    "from_user": self.user_id
                }
            )
        else:
            # Send group message to everyone
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "group_message",
                    "message": message,
                    "from_user": self.user_id
                }
            )

    async def group_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "group",
            "message": event["message"],
            "from_user": event["from_user"]
        }))

    async def private_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "private",
            "message": event["message"],
            "from_user": event["from_user"]
        }))

    async def disconnect(self, close_code):
        # Leave public chat group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        # Leave private group
        if self.user_id:
            await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)

        print(f"❌ Disconnected user {self.user_id}")
