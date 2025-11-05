from django.contrib import admin
from .models import ChatMessage, Alert, SkillProgress, Milestone, ProgressMonitoring, AIResponse, SessionPrompt, SessionNoteFlow

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


@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    """Admin interface for AI Response tracking"""
    list_display = ('id', 'response_type', 'user', 'session', 'model_used', 'is_successful', 
                   'created_at', 'get_truncated_prompt_display', 'get_truncated_response_display')
    list_filter = ('response_type', 'is_successful', 'model_used', 'created_at', 'user')
    search_fields = ('user__username', 'user__name', 'prompt', 'response', 'session__id')
    readonly_fields = ('created_at', 'updated_at', 'get_full_prompt', 'get_full_response')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Response Information', {
            'fields': ('response_type', 'user', 'session', 'is_successful', 'error_message')
        }),
        ('Input & Output', {
            'fields': ('get_full_prompt', 'get_full_response'),
            'classes': ('wide',)
        }),
        ('AI Metadata', {
            'fields': ('model_used', 'tokens_used', 'processing_time', 'context_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_truncated_prompt_display(self, obj):
        return obj.get_truncated_prompt()
    get_truncated_prompt_display.short_description = 'Prompt (Preview)'
    
    def get_truncated_response_display(self, obj):
        return obj.get_truncated_response()
    get_truncated_response_display.short_description = 'Response (Preview)'
    
    def get_full_prompt(self, obj):
        return obj.prompt
    get_full_prompt.short_description = 'Full Prompt'
    
    def get_full_response(self, obj):
        return obj.response
    get_full_response.short_description = 'Full Response'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'session')
    
    def has_add_permission(self, request):
        # Prevent manual creation - responses should only be created via API
        return False
    
    def has_change_permission(self, request, obj=None):
        # Allow viewing but prevent editing
        return False


@admin.register(SessionPrompt)
class SessionPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'prompt_type', 'is_responded', 'created_at', 'responded_at')
    list_filter = ('prompt_type', 'is_responded', 'created_at')
    search_fields = ('session__id', 'message', 'response')
    readonly_fields = ('created_at', 'responded_at')


@admin.register(SessionNoteFlow)
class SessionNoteFlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'is_note_completed', 'rbt_reviewed', 'final_note_submitted', 
                   'bcba_analyzed_by', 'created_at')
    list_filter = ('is_note_completed', 'rbt_reviewed', 'final_note_submitted', 'created_at')
    search_fields = ('session__id', 'note_content', 'ai_generated_note', 'bcba_analysis')
    readonly_fields = ('created_at', 'updated_at', 'bcba_analyzed_at')
