from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet, AlertViewSet

router = DefaultRouter()
# router.register(r'chat', ChatMessageViewSet, basename="chat")
# router.register(r'alerts', AlertViewSet, basename="alerts")

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', ChatMessageViewSet.as_view({'post': 'send'}), name='chat'),
    path('alerts/', AlertViewSet.as_view({'get': 'my_alerts'}), name='alerts-list'),
]
