from django.contrib import admin
from django.utils.html import format_html
from .models import TreatmentPlan, TreatmentGoal, TreatmentPlanApproval

class TreatmentGoalInline(admin.TabularInline):
    model = TreatmentGoal
    extra = 1
    fields = ['goal_description', 'mastery_criteria', 'custom_mastery_criteria', 'priority', 'is_achieved']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 'client_id', 'bcba', 'plan_type', 'status', 'priority', 
        'created_at', 'get_goals_count'
    ]
    list_filter = ['status', 'priority', 'plan_type', 'created_at', 'bcba']
    search_fields = ['client_name', 'client_id', 'bcba__username', 'bcba__email']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'approved_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('client_name', 'client_id', 'bcba', 'plan_type', 'status', 'priority')
        }),
        ('Assessment Summary', {
            'fields': ('assessment_tools_used', 'client_strengths', 'areas_of_need'),
            'classes': ('collapse',)
        }),
        ('Intervention Strategies', {
            'fields': ('reinforcement_strategies', 'prompting_hierarchy', 'behavior_interventions'),
            'classes': ('collapse',)
        }),
        ('Data Collection', {
            'fields': ('data_collection_methods',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TreatmentGoalInline]
    
    def get_goals_count(self, obj):
        return obj.goals.count()
    get_goals_count.short_description = 'Goals Count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('goals')

@admin.register(TreatmentGoal)
class TreatmentGoalAdmin(admin.ModelAdmin):
    list_display = [
        'get_goal_preview', 'treatment_plan', 'mastery_criteria', 
        'priority', 'is_achieved', 'created_at'
    ]
    list_filter = ['priority', 'is_achieved', 'created_at', 'treatment_plan__bcba']
    search_fields = ['goal_description', 'treatment_plan__client_name', 'treatment_plan__client_id']
    readonly_fields = ['created_at', 'updated_at', 'achieved_date']
    
    fieldsets = (
        ('Goal Information', {
            'fields': ('treatment_plan', 'goal_description', 'mastery_criteria', 'custom_mastery_criteria', 'priority')
        }),
        ('Progress Tracking', {
            'fields': ('is_achieved', 'achieved_date', 'progress_notes'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_goal_preview(self, obj):
        return obj.goal_description[:50] + "..." if len(obj.goal_description) > 50 else obj.goal_description
    get_goal_preview.short_description = 'Goal Description'

@admin.register(TreatmentPlanApproval)
class TreatmentPlanApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'treatment_plan', 'approver', 'approved', 'approved_at'
    ]
    list_filter = ['approved', 'approved_at', 'approver']
    search_fields = [
        'treatment_plan__client_name', 'treatment_plan__client_id', 
        'approver__username', 'approver__email'
    ]
    readonly_fields = ['approved_at']
    
    fieldsets = (
        ('Approval Information', {
            'fields': ('treatment_plan', 'approver', 'approved', 'approval_notes')
        }),
        ('Timestamps', {
            'fields': ('approved_at',),
            'classes': ('collapse',)
        }),
    )
