from django.contrib import admin
from .models import ChatMessage, Alert

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'message', 'is_read', 'due_date')
    list_filter = ('type', 'is_read')
