from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for nested resources
router = DefaultRouter()

app_name = 'session'

urlpatterns = [
    # Main session endpoints
    path('sessions/', views.SessionListView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session-detail'),
    path('sessions/start-from-schedule/', views.start_session_from_schedule, name='start-from-schedule'),
    path('upcoming-sessions/', views.upcoming_sessions, name='upcoming-sessions'),
    path('completed-sessions/', views.completed_sessions, name='completed-sessions'),
    path('all-sessions-details/', views.all_sessions_with_details, name='all-sessions-details'),
    path('sessions/<int:session_id>/details/', views.get_session_details, name='session-details'),
    path('sessions/statistics/', views.session_statistics, name='session-statistics'),
    path('sessions/user-sessions/', views.get_user_sessions, name='user-sessions'),
    path('users/<int:user_id>/details/', views.get_user_details, name='user-details'),
    path('bcba/clients/', views.get_bcba_clients, name='bcba-clients'),
    path('treatment-plan/<int:client_id>/session-data/', views.get_treatment_plan_for_session, name='treatment-plan-session-data'),
    path('sessions/<int:session_id>/treatment-plan-data/', views.get_session_treatment_plan_data, name='session-treatment-plan-data'),
    path('clients/<int:client_id>/treatment-plan-details/', views.get_client_treatment_plan_details, name='client-treatment-plan-details'),
    
    # Session timer endpoints
    path('sessions/<int:session_id>/timer/', views.SessionTimerView.as_view(), name='session-timer'),
    
    # Session form data endpoints
    path('sessions/<int:session_id>/additional-time/', views.AdditionalTimeView.as_view(), name='additional-time'),
    path('sessions/<int:session_id>/checklist/', views.PreSessionChecklistView.as_view(), name='pre-session-checklist'),
    path('sessions/<int:session_id>/activities/', views.ActivityView.as_view(), name='activities'),
    path('sessions/<int:session_id>/reinforcement-strategies/', views.ReinforcementStrategyView.as_view(), name='reinforcement-strategies'),
    path('sessions/<int:session_id>/abc-events/', views.ABCEventView.as_view(), name='abc-events'),
    path('sessions/<int:session_id>/goal-progress/', views.GoalProgressView.as_view(), name='goal-progress'),
    path('sessions/<int:session_id>/incidents/', views.IncidentView.as_view(), name='incidents'),
    path('sessions/<int:session_id>/notes/', views.SessionNoteView.as_view(), name='session-notes'),
    
    # Session actions
    path('sessions/submit/', views.submit_session, name='submit-session'),
    path('sessions/preview/', views.preview_session, name='preview-session'),
    path('sessions/<int:session_id>/save-and-generate-notes/', views.save_session_data_and_generate_notes, name='save-and-generate-notes'),
    path('sessions/<int:session_id>/generate-notes/', views.generate_ai_session_notes, name='generate-ai-notes'),
    
    # Ocean AI Integration endpoints
    path('sessions/<int:session_id>/ocean-dashboard/', views.get_session_dashboard_with_ocean, name='ocean-dashboard'),
    path('sessions/<int:session_id>/ocean-prompt/', views.create_ocean_prompt, name='create-ocean-prompt'),
    path('sessions/<int:session_id>/ocean-prompt/<int:prompt_id>/respond/', views.respond_to_ocean_prompt, name='respond-ocean-prompt'),
    path('sessions/<int:session_id>/ocean-ai-note/', views.generate_ocean_ai_note, name='generate-ocean-ai-note'),
    path('sessions/<int:session_id>/ocean-finalize/', views.finalize_session_with_ocean, name='ocean-finalize'),
    
    # Time Tracker endpoints
    path('time-trackers/', views.TimeTrackerView.as_view(), name='time-tracker-list'),
    path('time-trackers/<int:pk>/', views.TimeTrackerDetailView.as_view(), name='time-tracker-detail'),
    path('time-trackers/summary/', views.time_tracker_summary, name='time-tracker-summary'),

    # AI suggestion question endpoint
    path('ai-suggestions/<int:treatment_plan_id>/', views.AISuggestionView.as_view(), name='ai-suggestions'),
    path('bcba-client-sessions/', views.bcba_client_sessions, name='bcba-client-sessions'),
]
