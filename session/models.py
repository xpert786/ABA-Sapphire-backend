from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

User = get_user_model()

class Session(models.Model):
    """Main session model for therapy sessions"""
    SESSION_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='session_logs_as_client',
        limit_choices_to={'role__name': 'Clients/Parent'}
    )
    
    staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='session_logs_as_staff',
        limit_choices_to={'role__name__in': ['RBT', 'BCBA']}
    )
    
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='scheduled')
    session_notes = models.TextField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    service_type = models.CharField(max_length=100, blank=True, null=True)  # e.g., 'ABA'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session_date', 'start_time']
        unique_together = ['staff', 'session_date', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.client.username} - {self.session_date} ({self.start_time}-{self.end_time})"

class SessionTimer(models.Model):
    """Model to track session timer state"""
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='timer')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_running = models.BooleanField(default=False)
    total_duration = models.DurationField(default=timedelta(seconds=0))

    @property
    def current_duration(self):
        if self.start_time and self.is_running:
            from django.utils import timezone
            return timezone.now() - self.start_time
        return self.total_duration

    def __str__(self):
        return f"Timer for {self.session}"

class AdditionalTime(models.Model):
    """Model for additional time entries"""
    TIME_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('indirect', 'Indirect'),
        ('supervision', 'Supervision'),
    ]
    
    UNIT_CHOICES = [
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
    ]
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='additional_times')
    time_type = models.CharField(max_length=20, choices=TIME_TYPE_CHOICES, default='direct')
    duration = models.PositiveIntegerField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='minutes')
    reason = models.TextField()
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_time_type_display()} - {self.duration} {self.unit}"

class PreSessionChecklist(models.Model):
    """Model for pre-session checklist items"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='checklist_items')
    item_name = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.item_name} - {'✓' if self.is_completed else '✗'}"

class Activity(models.Model):
    """Model for session activities"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='activities')
    activity_name = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(480)])
    reinforcement_strategies = models.TextField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.activity_name} ({self.duration_minutes} min)"

class ReinforcementStrategy(models.Model):
    """Model for reinforcement strategies used"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='reinforcement_strategies')
    strategy_type = models.CharField(max_length=255)
    frequency = models.PositiveIntegerField()
    pr_ratio = models.PositiveIntegerField()  # PR = Positive Reinforcement ratio
    notes = models.TextField()

    def __str__(self):
        return f"{self.strategy_type} (PR: {self.pr_ratio})"

class ABCEvent(models.Model):
    """Model for ABC (Antecedent-Behavior-Consequence) events"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='abc_events')
    antecedent = models.TextField()
    behavior = models.TextField()
    consequence = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ABC Event - {self.behavior[:50]}..."

class GoalProgress(models.Model):
    """Model for tracking goal progress"""
    IMPLEMENTATION_CHOICES = [
        ('verbal', 'Verbal'),
        ('visual', 'Visual'),
        ('physical', 'Physical'),
        ('combination', 'Combination'),
    ]
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='goal_progress')
    goal_description = models.TextField()
    is_met = models.BooleanField()
    implementation_method = models.CharField(max_length=20, choices=IMPLEMENTATION_CHOICES)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.goal_description[:50]}... - {'Met' if self.is_met else 'Not Met'}"

class Incident(models.Model):
    """Model for incidents and crisis details"""
    INCIDENT_TYPE_CHOICES = [
        ('sib', 'SIB/Self-Injurious Behavior'),
        ('aggression', 'Aggression'),
        ('elopement', 'Elopement'),
        ('major_disruption', 'Major Disruption'),
        ('minor_disruption', 'Minor Disruption'),
        ('odr', 'ODR'),
        ('ir', 'IR'),
        ('crisis', 'CRISIS'),
    ]
    
    BEHAVIOR_SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPE_CHOICES)
    behavior_severity = models.CharField(max_length=20, choices=BEHAVIOR_SEVERITY_CHOICES)
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.get_behavior_severity_display()}"

class SessionNote(models.Model):
    """Model for general session notes"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='notes')
    note_content = models.TextField()
    note_type = models.CharField(max_length=50, default='general')  # general, ai_generated, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.session} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class TimeTracker(models.Model):
    """Model for manual time tracking entries"""
    TIME_TYPE_CHOICES = [
        ('direct', 'Direct Therapy'),
        ('indirect', 'Indirect Therapy'),
        ('supervision', 'Supervision'),
        ('documentation', 'Documentation'),
        ('travel', 'Travel Time'),
        ('training', 'Training'),
        ('meeting', 'Meeting'),
    ]
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='time_trackers')
    time_type = models.CharField(max_length=20, choices=TIME_TYPE_CHOICES, default='direct')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_time_trackers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def duration(self):
        """Calculate duration in minutes"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 60
        return 0

    @property
    def duration_display(self):
        """Display duration in HH:MM format"""
        duration_minutes = self.duration
        hours = int(duration_minutes // 60)
        minutes = int(duration_minutes % 60)
        return f"{hours:02d}:{minutes:02d}"

    def clean(self):
        """Validate that end_time is after start_time"""
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_time_type_display()} - {self.session} ({self.duration_display})"

    class Meta:
        ordering = ['-start_time']
        verbose_name = "Time Tracker Entry"
        verbose_name_plural = "Time Tracker Entries"
