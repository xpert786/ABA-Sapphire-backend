from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import json

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
    
    PLAN_TYPE_CHOICES = [
        ('comprehensive_aba', 'Comprehensive ABA'),
        ('behavior_reduction_focus', 'Behavior Reduction Focus'),
        ('social_skills_development', 'Social Skills Development'),
        ('communication_language', 'Communication & Language'),
        ('early_intervention', 'Early Intervention'),
        ('school_based_support', 'School-Based Support'),
        ('parent_training_focus', 'Parent Training Focus'),
        ('transition_planning', 'Transition Planning'),
    ]
    
    # Basic Information
    client_name = models.CharField(max_length=255, help_text="Name of the client")
    client_id = models.CharField(max_length=100, unique=True, help_text="Unique client identifier")
    bcba = models.ForeignKey(User, on_delete=models.CASCADE, related_name='treatment_plans', help_text="BCBA creating the plan")
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPE_CHOICES, default='comprehensive_aba', help_text="Type of treatment plan")
    
    # Assessment Summary
    assessment_tools_used = models.TextField(help_text="Assessment tools used (e.g., VB-MAPP, FBA, Clinical Observation)")
    assessment_tools = models.JSONField(default=list, blank=True, help_text="Array of assessment tools used")
    client_strengths = models.TextField(help_text="Client's strengths and abilities")
    areas_of_need = models.TextField(help_text="Areas where client needs support")
    
    # Intervention Strategies
    reinforcement_strategies = models.TextField(help_text="Reinforcement strategies to be used")
    reinforcement_strategies_array = models.JSONField(default=list, blank=True, help_text="Array of reinforcement strategies with details")
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
    
    def get_assessment_tools_list(self):
        """Get assessment tools as a list"""
        if isinstance(self.assessment_tools, str):
            try:
                return json.loads(self.assessment_tools)
            except json.JSONDecodeError:
                return []
        return self.assessment_tools or []
    
    def set_assessment_tools_list(self, tools_list):
        """Set assessment tools from a list"""
        self.assessment_tools = tools_list
    
    def get_reinforcement_strategies_list(self):
        """Get reinforcement strategies as a list"""
        if isinstance(self.reinforcement_strategies_array, str):
            try:
                return json.loads(self.reinforcement_strategies_array)
            except json.JSONDecodeError:
                return []
        return self.reinforcement_strategies_array or []
    
    def set_reinforcement_strategies_list(self, strategies_list):
        """Set reinforcement strategies from a list"""
        self.reinforcement_strategies_array = strategies_list
    
    def add_assessment_tool(self, tool_name):
        """Add a single assessment tool to the list"""
        tools = self.get_assessment_tools_list()
        if tool_name not in tools:
            tools.append(tool_name)
            self.set_assessment_tools_list(tools)
    
    def add_reinforcement_strategy(self, strategy_data):
        """Add a reinforcement strategy to the list"""
        strategies = self.get_reinforcement_strategies_list()
        strategies.append(strategy_data)
        self.set_reinforcement_strategies_list(strategies)

    def __str__(self):
        return f"Treatment Plan for {self.client_name} ({self.client_id})"

class TreatmentGoal(models.Model):
    """Individual goals within a treatment plan"""
    
    MASTERY_CRITERIA_CHOICES = [
        ('80%_accuracy', '80% accuracy'),
        ('85%_accuracy', '85% accuracy'),
        ('90%_accuracy', '90% accuracy'),
        ('100%_accuracy', '100% accuracy'),
        ('8/10_opportunities', '8/10 opportunities'),
        ('9/10_opportunities', '9/10 opportunities'),
        ('4/5_opportunities', '4/5 opportunities'),
        ('5/5_opportunities', '5/5 opportunities'),
        ('3_consecutive_sessions', 'Across 3 consecutive sessions'),
        ('5_consecutive_sessions', 'Across 5 consecutive sessions'),
        ('2_consecutive_sessions', 'Across 2 consecutive sessions'),
        ('3+_activities_per_session', '3+ activities per session'),
        ('independent_in_80%_of_trials', 'Independent in 80% of trials'),
        ('independent_in_3_consecutive_sessions', 'Independent in 3 consecutive sessions'),
        ('generalized_across_people', 'Generalized across people'),
        ('generalized_across_settings', 'Generalized across settings'),
        ('generalized_across_materials', 'Generalized across materials'),
        ('maintained_for_2_weeks', 'Maintained for 2 weeks'),
        ('maintained_for_1_month', 'Maintained for 1 month'),
        ('reduced_by_50%', 'Behavior reduced by 50% from baseline'),
        ('reduced_by_80%', 'Behavior reduced by 80% from baseline'),
        ('less_than_1_occurrence_per_day', 'Less than 1 occurrence per day'),
        ('within_10_seconds_of_instruction', 'Response within 10 seconds of instruction'),
        ('spontaneous_3_times_per_session', 'Spontaneous 3 times per session'),
        ('2_successful_generalization_sessions', '2 successful generalization sessions'),
        ('no_prompts_in_3_consecutive_sessions', 'No prompts in 3 consecutive sessions'),
        ('partial_prompt_fade_to_independent', 'Partial prompt faded to independent'),
        ('latency_under_5_seconds', 'Latency under 5 seconds'),
        ('meets_goal_for_2_weeks', 'Meets goal for 2 consecutive weeks'),
        ('criterion_met_for_80%_of_targets', 'Criterion met for 80% of targets'),
        ('criterion_met_for_all_targets', 'Criterion met for all targets'),
        ('80%_accuracy_for_2_consecutive_sessions', '80% accuracy for 2 consecutive sessions'),
        ('80%_accuracy_for_3_consecutive_sessions', '80% accuracy for 3 consecutive sessions'),
        ('90%_accuracy_for_3_consecutive_sessions', '90% accuracy for 3 consecutive sessions'),
        ('custom', 'Custom criteria'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    treatment_plan = models.ForeignKey(TreatmentPlan, on_delete=models.CASCADE, related_name='goals')
    goal_description = models.TextField(help_text="Detailed description of the goal")
    mastery_criteria = models.CharField(max_length=250, choices=MASTERY_CRITERIA_CHOICES, help_text="Criteria for goal mastery")
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
