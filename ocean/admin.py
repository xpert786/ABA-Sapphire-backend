from django.contrib import admin
from .models import ChatMessage, Alert, SkillProgress, Milestone, ProgressMonitoring

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'created_at')
    readonly_fields = ('created_at',)
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__name', 'message')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'message', 'is_read', 'due_date')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__name', 'message')

class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 1
    fields = ('milestone_title', 'milestone_description', 'achieved_date', 'is_verified', 'verified_by')
    readonly_fields = ('verified_at',)

@admin.register(SkillProgress)
class SkillProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'skill_category', 'skill_name', 'progress_percentage', 'updated_at')
    list_filter = ('skill_category', 'treatment_plan', 'created_at', 'updated_at')
    search_fields = ('client__username', 'client__name', 'skill_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MilestoneInline]
    
    fieldsets = (
        ('Client & Treatment Plan', {
            'fields': ('client', 'treatment_plan')
        }),
        ('Skill Information', {
            'fields': ('skill_category', 'skill_name', 'description')
        }),
        ('Progress Tracking', {
            'fields': ('progress_percentage', 'current_level', 'target_level')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'treatment_plan')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'milestone_title', 'skill_progress', 'achieved_date', 'is_verified', 'verified_by')
    list_filter = ('is_verified', 'achieved_date', 'created_at')
    search_fields = ('milestone_title', 'milestone_description', 'skill_progress__skill_name')
    readonly_fields = ('created_at', 'verified_at')
    
    fieldsets = (
        ('Milestone Details', {
            'fields': ('skill_progress', 'milestone_title', 'milestone_description', 'achieved_date')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.is_verified and not obj.verified_by:
            obj.verified_by = request.user
            from django.utils import timezone
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('skill_progress', 'skill_progress__client', 'verified_by')

@admin.register(ProgressMonitoring)
class ProgressMonitoringAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'treatment_plan', 'period_start', 'period_end', 
                   'session_attendance_rate', 'goal_achievement_rate', 'calculated_at')
    list_filter = ('period_start', 'period_end', 'calculated_at', 'treatment_plan')
    search_fields = ('client__username', 'client__name', 'treatment_plan__client_name', 'notes')
    readonly_fields = ('calculated_at', 'updated_at')
    date_hierarchy = 'period_end'
    
    fieldsets = (
        ('Client & Treatment Plan', {
            'fields': ('client', 'treatment_plan')
        }),
        ('Period Information', {
            'fields': ('period_start', 'period_end')
        }),
        ('Key Performance Indicators (KPIs)', {
            'fields': (
                'session_attendance_rate',
                'goal_achievement_rate',
                'behavior_incidents_per_week',
                'engagement_rate'
            )
        }),
        ('Change from Last Month', {
            'fields': (
                'attendance_change',
                'goal_achievement_change',
                'incidents_change',
                'engagement_change'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('calculated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'treatment_plan')
