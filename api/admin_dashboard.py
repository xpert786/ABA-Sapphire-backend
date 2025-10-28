from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from .models import CustomUser
from scheduler.models import Session
from session.models import Session as TherapySession

class AdminDashboardMixin:
    """Mixin to add dashboard functionality to admin"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view for admins"""
        context = {
            'title': 'Admin Dashboard',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        # User statistics
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(status='Active').count()
        pending_users = CustomUser.objects.filter(status='Pending').count()
        
        # Role-based statistics
        role_stats = CustomUser.objects.values('role__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Session statistics
        total_sessions = Session.objects.count()
        upcoming_sessions = Session.objects.filter(
            session_date__gte=timezone.now().date()
        ).count()
        
        # Recent activity
        recent_users = CustomUser.objects.order_by('-date_joined')[:10]
        recent_sessions = Session.objects.order_by('-created_at')[:10]
        
        context.update({
            'total_users': total_users,
            'active_users': active_users,
            'pending_users': pending_users,
            'role_stats': role_stats,
            'total_sessions': total_sessions,
            'upcoming_sessions': upcoming_sessions,
            'recent_users': recent_users,
            'recent_sessions': recent_sessions,
        })
        
        return render(request, 'admin/dashboard.html', context)

# Apply the mixin to CustomUserAdmin
from .admin import CustomUserAdmin
CustomUserAdmin.__bases__ = (AdminDashboardMixin,) + CustomUserAdmin.__bases__
