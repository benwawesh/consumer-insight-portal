"""
URL configuration for affiliate project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from insights import views as insights_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', insights_views.home_view, name='home'),
    path('offers/', insights_views.offers_view, name='offers'),
    path('task/<str:offer_id>/', insights_views.task_view, name='task'),
    path('task/', insights_views.task_view, name='task_random'),
    path('verification/', insights_views.verification_view, name='verification'),
    path('callback/', insights_views.conversion_callback, name='callback'),
    path('admin/sync-offers/', insights_views.sync_offers_view, name='admin:sync_offers'),
    path('admin/revenue-dashboard/', insights_views.revenue_dashboard_view, name='admin:revenue_dashboard'),
]

# Custom error pages
handler404 = insights_views.custom_404
handler500 = insights_views.custom_500

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)