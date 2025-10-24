from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class TreatmentPlan(models.Model):
    """BCBA Treatment Plan for clients"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Basic Information
    client_name = models.CharField(max_length=255, help_text="Name of the client")
    client_id = models.CharField(max_length=100, unique=True, help_text="Unique client identifier")
    bcba = models.ForeignKey(User, on_delete=models.CASCADE, related_name='treatment_plans', help_text="BCBA creating the plan")
    
    # Assessment Summary
    assessment_tools_used = models.TextField(help_text="Assessment tools used (e.g., VB-MAPP, FBA, Clinical Observation)")
    client_strengths = models.TextField(help_text="Client's strengths and abilities")
    areas_of_need = models.TextField(help_text="Areas where client needs support")
    
    # Intervention Strategies
    reinforcement_strategies = models.TextField(help_text="Reinforcement strategies to be used")
    prompting_hierarchy = models.TextField(help_text="Prompting hierarchy approach")
    behavior_interventions = models.TextField(help_text="Behavior intervention strategies")
    
    # Data Collection
    data_collection_methods = models.TextField(help_text="Data collection methods for RBT")
    
    # Plan Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Treatment Plan"
        verbose_name_plural = "Treatment Plans"
    
    def __str__(self):
        return f"Treatment Plan for {self.client_name} ({self.client_id})"

class TreatmentGoal(models.Model):
    """Individual goals within a treatment plan"""
    
    MASTERY_CRITERIA_CHOICES = [
        ('8/10_opportunities', '8/10 opportunities'),
        ('3+_activities_per_session', '3+ activities per session'),
        ('80%_accuracy', '80% accuracy'),
        ('90%_accuracy', '90% accuracy'),
        ('100%_accuracy', '100% accuracy'),
        ('custom', 'Custom criteria'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    treatment_plan = models.ForeignKey(TreatmentPlan, on_delete=models.CASCADE, related_name='goals')
    goal_description = models.TextField(help_text="Detailed description of the goal")
    mastery_criteria = models.CharField(max_length=50, choices=MASTERY_CRITERIA_CHOICES, help_text="Criteria for goal mastery")
    custom_mastery_criteria = models.TextField(blank=True, null=True, help_text="Custom mastery criteria if 'custom' is selected")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Goal tracking
    is_achieved = models.BooleanField(default=False)
    achieved_date = models.DateTimeField(null=True, blank=True)
    progress_notes = models.TextField(blank=True, help_text="Notes on goal progress")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'created_at']
        verbose_name = "Treatment Goal"
        verbose_name_plural = "Treatment Goals"
    
    def __str__(self):
        return f"Goal: {self.goal_description[:50]}..."

class TreatmentPlanApproval(models.Model):
    """Track approval workflow for treatment plans"""
    
    treatment_plan = models.OneToOneField(TreatmentPlan, on_delete=models.CASCADE, related_name='approval')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_plans')
    approved = models.BooleanField(default=False)
    approval_notes = models.TextField(blank=True, help_text="Notes from the approver")
    approved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Treatment Plan Approval"
        verbose_name_plural = "Treatment Plan Approvals"
    
    def __str__(self):
        status = "Approved" if self.approved else "Rejected"
        return f"{status} by {self.approver.get_full_name() or self.approver.username}"
