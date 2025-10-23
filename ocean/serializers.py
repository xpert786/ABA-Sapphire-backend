from rest_framework import serializers
from .models import ChatMessage, Alert, SessionPrompt, SessionNoteFlow


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'   # or list specific fields if you want
    def get_created_at_local(self, obj):
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S")

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'

class SessionPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionPrompt
        fields = '__all__'

class SessionNoteFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionNoteFlow
        fields = '__all__'
