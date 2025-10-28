from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    """
    One-to-one chat room between two users.
    """
    name = models.CharField(max_length=255, unique=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    """
    Messages inside a chat room.
    """
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} -> {self.room.name}: {self.content[:20]}"
