from django.urls import path
from . import views

urlpatterns = [
    # Treatment Plan URLs
    path('plans/', views.TreatmentPlanListCreateView.as_view(), name='treatment-plan-list-create'),
    path('plans/stats/', views.treatment_plan_stats, name='treatment-plan-stats'),
    
    # More specific paths first (before generic detail view)
    path('plans/<int:pk>/submit/', views.submit_treatment_plan, name='submit-treatment-plan'),
    path('plans/<int:pk>/approve/', views.approve_treatment_plan, name='approve-treatment-plan'),
    path('plans/<int:pk>/client/', views.get_client_from_treatment_plan, name='get-client-from-treatment-plan'),
    
    # Treatment Goal URLs
    path('plans/<int:treatment_plan_id>/goals/', views.TreatmentGoalListCreateView.as_view(), name='treatment-goal-list-create'),
    path('plans/<int:treatment_plan_id>/goals/<int:pk>/', views.TreatmentGoalDetailView.as_view(), name='treatment-goal-detail'),
    
    # Generic detail view (should be last)
    path('plans/<int:pk>/', views.TreatmentPlanDetailView.as_view(), name='treatment-plan-detail'),
    
    # Approval URLs
    path('approvals/', views.TreatmentPlanApprovalListView.as_view(), name='treatment-plan-approval-list'),
    
    # AI Goal Suggestions
    path('plans/goal-suggestions/', views.ai_goal_suggestions, name='ai-goal-suggestions'),
    path('plans/<int:pk>/goal-suggestions/', views.ai_goal_suggestions_for_plan, name='ai-goal-suggestions-for-plan'),
]
