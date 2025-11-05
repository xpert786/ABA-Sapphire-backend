from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet, AlertViewSet, SessionPromptViewSet, SessionNoteFlowViewSet, get_client_progress_monitoring, AIResponseViewSet

router = DefaultRouter()
router.register(r'chat-messages', ChatMessageViewSet, basename="chat-messages")
router.register(r'session-prompts', SessionPromptViewSet, basename="session-prompts")
router.register(r'session-notes', SessionNoteFlowViewSet, basename="session-notes")
router.register(r'ai-responses', AIResponseViewSet, basename="ai-responses")

urlpatterns = [
    path('', include(router.urls)),
    path('ws/chat/', ChatMessageViewSet.as_view({'post': 'send'}), name='ws-ws-chat'),
    path('alerts/', AlertViewSet.as_view({'get': 'my_alerts'}), name='alerts-list'),
    path('progress-monitoring/<int:client_id>/', get_client_progress_monitoring, name='client-progress-monitoring'),
]
