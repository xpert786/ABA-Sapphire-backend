from django.contrib import admin
from .models import Session, SessionLog, TimeTracker, Client

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'staff', 'treatment_plan', 'session_date', 'start_time', 'end_time', 'created_at')
    list_filter = ('session_date', 'staff', 'client', 'treatment_plan', 'created_at')
    search_fields = ('client__name', 'client__username', 'staff__name', 'staff__username', 'session_notes', 'treatment_plan__client_name')
    readonly_fields = ('created_at',)
    list_per_page = 25
    
    fieldsets = (
        ('Session Details', {
            'fields': ('client', 'staff', 'treatment_plan', 'session_date', 'start_time', 'end_time')
        }),
        ('Session Information', {
            'fields': ('session_notes', 'duration')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'staff', 'treatment_plan')

@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'behavior', 'created_at')
    list_filter = ('created_at', 'session__session_date')
    search_fields = ('behavior', 'antecedent', 'consequence', 'session__client__name')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__client')

@admin.register(TimeTracker)
class TimeTrackerAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'start_time', 'end_time', 'duration_display')
    list_filter = ('start_time', 'end_time')
    search_fields = ('session__client__name', 'session__staff__name')
    readonly_fields = ('duration_display',)
    
    def duration_display(self, obj):
        if obj.duration:
            return f"{obj.duration:.1f} minutes"
        return "Not completed"
    duration_display.short_description = "Duration"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__client', 'session__staff')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at',)