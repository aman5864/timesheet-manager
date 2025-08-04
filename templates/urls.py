from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

urlpatterns = [
    # Auth views
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/verify/', views.verify_otp, name='verify_otp'),

    path('', lambda request: redirect('login'), name='root_redirect'),

    # Timesheet views
    path('login/', views.custom_login_view, name='login'),
    path('week/', views.week_view, name='week_view'),
    path('week/<int:year>/<int:week>/', views.week_view, name='week_view_custom'),
    path('month/', views.month_view, name='month_view'),
    path('month/<int:year>/<int:month>/', views.month_view, name='month_view'),
    path('create/', views.create_entry, name='create_entry'),
    path('update/<int:pk>/', views.update_entry, name='update_entry'),
    path('delete/<int:pk>/', views.delete_entry, name='delete_entry'),
    path('export/month/<int:year>/<int:month>/', views.export_month_excel, name='export_month_excel'),
    path('api/is_weekend/', views.is_weekend, name='is_weekend'),
]
