from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main template app (UI + auth)
    path('', include('templates.urls')),  # <-- templates/views.py contains week_view etc.

    # Backend API or admin functions (optional)
    path('api/', include('timesheet_backend.urls')),  # If you have API endpoints later
]
