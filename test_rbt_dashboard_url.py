"""
Quick test script to verify RBT Dashboard URL is registered
Run this with: python manage.py shell < test_rbt_dashboard_url.py
Or: python manage.py shell, then paste the code
"""
from django.urls import reverse, resolve
from django.conf import settings

# Test if the URL can be resolved
try:
    url = reverse('rbt-dashboard')
    print(f"✓ URL resolved successfully: {url}")
    print(f"  Full URL would be: http://localhost:8000{url}")
except Exception as e:
    print(f"✗ URL resolution failed: {e}")

# Test if the view can be imported
try:
    from api.views import RBTDashboardView
    print("✓ RBTDashboardView imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")

# List all API URLs to verify
try:
    from django.urls import get_resolver
    from api import urls as api_urls
    
    print("\nAll API URL patterns:")
    for pattern in api_urls.urlpatterns:
        if hasattr(pattern, 'name') and pattern.name:
            print(f"  - {pattern.name}: {pattern.pattern}")
        else:
            print(f"  - {pattern.pattern}")
except Exception as e:
    print(f"Error listing URLs: {e}")

