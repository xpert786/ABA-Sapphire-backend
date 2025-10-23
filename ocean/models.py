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

class SessionPrompt(models.Model):
    """Model for tracking session prompts and interactions"""
    PROMPT_TYPES = [
        ("engagement", "Engagement Check"),
        ("note_reminder", "Note Reminder"),
        ("session_wrap", "Session Wrap-up"),
        ("goal_check", "Goal Progress Check"),
        ("behavior_tracking", "Behavior Tracking"),
    ]
    
    session = models.ForeignKey(
        'session.Session',
        on_delete=models.CASCADE,
        related_name="ocean_prompts"
    )
    prompt_type = models.CharField(max_length=20, choices=PROMPT_TYPES)
    message = models.TextField()
    response = models.TextField(blank=True, null=True)
    is_responded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_prompt_type_display()} - {self.session}"

class SessionNoteFlow(models.Model):
    """Model for tracking session note completion flow"""
    session = models.OneToOneField(
        'session.Session',
        on_delete=models.CASCADE,
        related_name="note_flow"
    )
    is_note_completed = models.BooleanField(default=False)
    note_content = models.TextField(blank=True, null=True)
    ai_generated_note = models.TextField(blank=True, null=True)
    rbt_reviewed = models.BooleanField(default=False)
    final_note_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note Flow - {self.session} ({'Completed' if self.final_note_submitted else 'In Progress'})"