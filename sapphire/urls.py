"""
URL configuration for sapphire project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('scheduler/', include('scheduler.urls')),
    path('session/', include('session.urls')),
    path('messaging/', include('messaging.urls')),
    path('ocean/', include('ocean.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
