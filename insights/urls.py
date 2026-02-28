"""
URL configuration for insights app.
"""
from django.urls import path
from . import views

app_name = 'insights'

urlpatterns = [
    # Public views
    path('', views.home_view, name='home'),
    path('offers/', views.offers_view, name='offers'),
    path('task/<str:offer_id>/', views.task_view, name='task'),
    path('task/', views.task_view, name='task_random'),
    path('verification/', views.verification_view, name='verification'),
    
    # Callback endpoint
    path('callback/', views.conversion_callback, name='callback'),
]