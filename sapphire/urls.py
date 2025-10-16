"""
URL configuration for sapphire project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('sapphire/admin/', admin.site.urls),
    path('sapphire/api/', include('api.urls')),
    path('sapphire/scheduler/', include('scheduler.urls')),
    path('sapphire/session/', include('session.urls')),
    path('sapphire/messaging/', include('messaging.urls')),
    path('sapphire/ocean/', include('ocean.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
