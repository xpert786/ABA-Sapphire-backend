import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Optional: handle messages from frontend
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({"message": f"Echo: {data.get('prompt')}" }))

    # Called by server to push updates
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def alert_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
