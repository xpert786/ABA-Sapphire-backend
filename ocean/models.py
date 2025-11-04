from django.db import models
from django.conf import settings  # use custom user model
from django.core.validators import MinValueValidator, MaxValueValidator

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
    
    # BCBA Analysis fields
    bcba_analysis = models.TextField(blank=True, null=True, help_text="BCBA supervisory analysis and review notes")
    bcba_analyzed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bcba_analyses',
        limit_choices_to={'role__name': 'BCBA'},
        help_text="BCBA who generated the analysis"
    )
    bcba_analyzed_at = models.DateTimeField(null=True, blank=True, help_text="When BCBA analysis was generated")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note Flow - {self.session} ({'Completed' if self.final_note_submitted else 'In Progress'})"


class SkillProgress(models.Model):
    """Model for tracking skill area progress over time"""
    SKILL_CATEGORIES = [
        ('communication', 'Communication Skills'),
        ('social_interaction', 'Social Interaction'),
        ('behavior_management', 'Behavior Management'),
        ('academic_skills', 'Academic Skills'),
        ('daily_living', 'Daily Living Skills'),
        ('motor_skills', 'Motor Skills'),
        ('adaptive_behavior', 'Adaptive Behavior'),
        ('play_skills', 'Play Skills'),
        ('vocational', 'Vocational Skills'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_progress',
        limit_choices_to={'role__name': 'Clients/Parent'}
    )
    treatment_plan = models.ForeignKey(
        'treatment_plan.TreatmentPlan',
        on_delete=models.CASCADE,
        related_name='skill_progress',
        null=True,
        blank=True
    )
    skill_category = models.CharField(max_length=30, choices=SKILL_CATEGORIES)
    skill_name = models.CharField(max_length=255, help_text="Name of the specific skill")
    description = models.TextField(help_text="Description of the skill and progress")
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage (0-100)"
    )
    current_level = models.CharField(max_length=100, blank=True, help_text="Current skill level")
    target_level = models.CharField(max_length=100, blank=True, help_text="Target skill level")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at', '-created_at']
        verbose_name = "Skill Progress"
        verbose_name_plural = "Skill Progress"
        unique_together = ['client', 'treatment_plan', 'skill_category', 'skill_name']
    
    def __str__(self):
        return f"{self.client.username} - {self.get_skill_category_display()}: {self.progress_percentage}%"


class Milestone(models.Model):
    """Model for tracking milestones/achievements in skill progress"""
    skill_progress = models.ForeignKey(
        SkillProgress,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    milestone_title = models.CharField(max_length=255, help_text="Title of the milestone")
    milestone_description = models.TextField(blank=True, help_text="Description of what was achieved")
    achieved_date = models.DateField(help_text="Date when milestone was achieved")
    is_verified = models.BooleanField(default=False, help_text="Whether BCBA has verified this milestone")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_milestones',
        limit_choices_to={'role__name': 'BCBA'}
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-achieved_date', '-created_at']
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
    
    def __str__(self):
        return f"{self.milestone_title} - {self.skill_progress.client.username}"


class ProgressMonitoring(models.Model):
    """Model for storing calculated progress monitoring data for clients"""
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress_monitoring',
        limit_choices_to={'role__name': 'Clients/Parent'}
    )
    treatment_plan = models.ForeignKey(
        'treatment_plan.TreatmentPlan',
        on_delete=models.CASCADE,
        related_name='progress_monitoring',
        null=True,
        blank=True
    )
    
    # KPIs - stored as calculated values
    session_attendance_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Session attendance percentage (0-100)"
    )
    goal_achievement_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Goal achievement percentage (0-100)"
    )
    behavior_incidents_per_week = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Average behavior incidents per week"
    )
    engagement_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Engagement rate percentage (0-100)"
    )
    
    # Comparison metrics (from last month)
    attendance_change = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Change in attendance from last month (% points)"
    )
    goal_achievement_change = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Change in goal achievement from last month (% points)"
    )
    incidents_change = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Change in incidents per week from last month"
    )
    engagement_change = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Change in engagement from last month (% points)"
    )
    
    # Date range for this monitoring period
    period_start = models.DateField(help_text="Start date of monitoring period")
    period_end = models.DateField(help_text="End date of monitoring period")
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Additional notes about progress")
    
    class Meta:
        ordering = ['-period_end', '-calculated_at']
        verbose_name = "Progress Monitoring"
        verbose_name_plural = "Progress Monitoring"
        unique_together = ['client', 'treatment_plan', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.client.username} - {self.period_start} to {self.period_end}"