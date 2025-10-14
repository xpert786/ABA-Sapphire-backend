from django.db import models
from django.conf import settings  # use custom user model

class ChatMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # will point to api.CustomUser
        on_delete=models.CASCADE,
        related_name="messages"
    )
    message = models.TextField()
    response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message[:30]}"

class Alert(models.Model):
    ALERT_TYPES = [
        ("CLAIM", "Claim"),
        ("NOTE", "Note Reminder"),
        ("PAYROLL", "Payroll Task"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alerts"
    )
    type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.CharField(max_length=255)
    due_date = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.message[:30]}"
