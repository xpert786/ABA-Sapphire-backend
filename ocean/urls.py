from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet, AlertViewSet, SessionPromptViewSet, SessionNoteFlowViewSet

router = DefaultRouter()
router.register(r'session-prompts', SessionPromptViewSet, basename="session-prompts")
router.register(r'session-notes', SessionNoteFlowViewSet, basename="session-notes")

urlpatterns = [
    path('', include(router.urls)),
    path('ws/chat/', ChatMessageViewSet.as_view({'post': 'send'}), name='ws-ws-chat'),
    path('alerts/', AlertViewSet.as_view({'get': 'my_alerts'}), name='alerts-list'),
]
