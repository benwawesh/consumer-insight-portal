from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import CachedOffer, ConversionTracking, AdminSettings
from .services import get_offer_with_tracking, get_offer_by_id_with_tracking, fetch_and_cache_offers
from .utils import (
    generate_tracking_id,
    get_client_ip,
    get_user_agent,
    get_referrer,
    detect_device_type,
    detect_bot,
    log_conversion_event
)

logger = logging.getLogger('insights')


def home_view(request):
    """
    Home/Landing page with professional introduction
    """
    context = {
        'page_title': 'Consumer Insight Portal',
    }
    return render(request, 'home.html', context)


def offers_view(request):
    """
    Display available offers list
    Only shows approved (live) offers
    """
    from .services import CPAGripAPIService
    service = CPAGripAPIService()
    live_offers = service.get_all_live_offers()
    
    context = {
        'page_title': 'Available Offers',
        'offers': live_offers,
        'total_offers': live_offers.count(),
    }
    return render(request, 'offers.html', context)


def task_view(request, offer_id=None):
    """
    Task environment with iframe
    Generates tracking_id and creates conversion record
    """
    # Get user information
    user_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    referrer = get_referrer(request)
    device_type = detect_device_type(user_agent)
    
    # Check for bot traffic
    is_bot = detect_bot(user_agent)
    if is_bot:
        messages.warning(request, 'Unusual activity detected. Please contact support if this persists.')
        logger.warning(f"Bot traffic detected from IP: {user_ip}")
    
    # Generate tracking ID
    tracking_id = generate_tracking_id()
    
    # Get offer
    if offer_id:
        offer = get_offer_by_id_with_tracking(offer_id, tracking_id)
    else:
        offer = get_offer_with_tracking(tracking_id)
    
    if not offer:
        messages.error(request, 'No offers are currently available. Please check back later.')
        return redirect('offers')
    
    # Create conversion tracking record
    try:
        conversion = ConversionTracking.objects.create(
            tracking_id=tracking_id,
            offer_id=offer.offer_id,
            offer_name=offer.name,
            payout=offer.payout,
            user_ip=user_ip,
            device_type=device_type,
            user_agent=user_agent,
            referrer=referrer,
            status='pending'
        )
        
        log_conversion_event('task_entered', tracking_id, {
            'offer_id': offer.offer_id,
            'ip': user_ip,
            'device': device_type
        })
        
    except Exception as e:
        logger.error(f"Error creating conversion record: {e}")
        messages.error(request, 'An error occurred. Please try again.')
        return redirect('offers')
    
    context = {
        'page_title': f'Task - {offer.name}',
        'offer': offer,
        'tracking_id': tracking_id,
        'device_type': device_type,
    }
    return render(request, 'task.html', context)


def verification_view(request):
    """
    3-step verification progress page
    """
    context = {
        'page_title': 'Verification Progress',
    }
    return render(request, 'verification.html', context)


@csrf_exempt
def conversion_callback(request):
    """
    CPAGrip Global Postback callback endpoint
    Receives GET request with conversion details and updates status
    """
    if request.method != 'GET':
        return HttpResponse('Method not allowed', status=405)
    
    # Extract parameters from CPAGrip
    tracking_id = request.GET.get('tracking_id')
    payout = request.GET.get('payout')
    offer_id = request.GET.get('offer_id')
    status = request.GET.get('status', 'completed')
    
    if not tracking_id:
        logger.error("Callback received without tracking_id")
        return HttpResponse('MISSING_TRACKING_ID', status=400)
    
    try:
        # Find conversion by tracking_id
        conversion = ConversionTracking.objects.get(
            tracking_id=tracking_id,
            status='pending'
        )
        
        # Update conversion status
        conversion.status = 'completed' if status.lower() == 'completed' else 'failed'
        conversion.completed_at = timezone.now()
        
        # Update payout if provided
        if payout:
            try:
                conversion.payout = Decimal(str(payout))
            except:
                pass
        
        conversion.save()
        
        log_conversion_event('callback_received', tracking_id, {
            'status': conversion.status,
            'payout': conversion.payout,
            'completed_at': conversion.completed_at
        })
        
        logger.info(f"Conversion updated: {tracking_id} -> {conversion.status}")
        return HttpResponse('SUCCESS')
        
    except ConversionTracking.DoesNotExist:
        logger.warning(f"Conversion not found or already processed: {tracking_id}")
        return HttpResponse('NOT_FOUND', status=404)
        
    except Exception as e:
        logger.error(f"Error processing callback for {tracking_id}: {e}")
        return HttpResponse('ERROR', status=500)


@staff_member_required
def sync_offers_view(request):
    """
    Manual sync trigger for Admin
    Fetches and caches new offers from CPAGrip
    """
    cached_count = fetch_and_cache_offers(status='pending')
    
    if cached_count is None:
        messages.error(request, 'Failed to sync offers from CPAGrip API. Please check logs.')
    elif cached_count == 0:
        messages.warning(request, 'No new offers found matching your criteria.')
    else:
        messages.success(
            request,
            f"Sync completed! {cached_count} new offers added to Review Queue."
        )
    
    return redirect('/admin/insights/cachedoffer/')


@staff_member_required
def revenue_dashboard_view(request):
    """
    Revenue Monitor Dashboard
    Shows daily earnings, conversions, and EPC
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    # Today's metrics
    today_conversions = ConversionTracking.objects.filter(
        status='completed',
        created_at__date=today
    )
    today_revenue = today_conversions.aggregate(
        total=Sum('payout')
    )['total'] or Decimal('0')
    today_count = today_conversions.count()
    
    # Yesterday's metrics (for comparison)
    yesterday_conversions = ConversionTracking.objects.filter(
        status='completed',
        created_at__date=yesterday
    )
    yesterday_revenue = yesterday_conversions.aggregate(
        total=Sum('payout')
    )['total'] or Decimal('0')
    
    # Weekly metrics
    week_conversions = ConversionTracking.objects.filter(
        status='completed',
        created_at__date__gte=week_ago
    )
    week_revenue = week_conversions.aggregate(
        total=Sum('payout')
    )['total'] or Decimal('0')
    week_count = week_conversions.count()
    
    # All-time metrics
    all_conversions = ConversionTracking.objects.filter(status='completed')
    total_revenue = all_conversions.aggregate(
        total=Sum('payout')
    )['total'] or Decimal('0')
    total_count = all_conversions.count()
    
    # Calculate EPC (Earnings Per Click)
    epc = week_revenue / week_count if week_count > 0 else Decimal('0')
    
    # Daily revenue for chart (last 7 days)
    daily_revenue = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        date_revenue = ConversionTracking.objects.filter(
            status='completed',
            created_at__date=date
        ).aggregate(total=Sum('payout'))['total'] or Decimal('0')
        daily_revenue.append({
            'date': date.strftime('%m/%d'),
            'revenue': float(date_revenue),
            'count': ConversionTracking.objects.filter(
                status='completed',
                created_at__date=date
            ).count()
        })
    
    # Offer performance (top 5 offers)
    top_offers = ConversionTracking.objects.filter(
        status='completed'
    ).values('offer_name').annotate(
        conversions=Count('id'),
        revenue=Sum('payout')
    ).order_by('-revenue')[:5]
    
    # Device type distribution
    device_stats = ConversionTracking.objects.filter(
        status='completed'
    ).values('device_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'page_title': 'Revenue Monitor',
        'today_revenue': float(today_revenue),
        'today_count': today_count,
        'yesterday_revenue': float(yesterday_revenue),
        'week_revenue': float(week_revenue),
        'week_count': week_count,
        'total_revenue': float(total_revenue),
        'total_count': total_count,
        'epc': float(epc),
        'daily_revenue': daily_revenue,
        'top_offers': top_offers,
        'device_stats': device_stats,
    }
    
    return render(request, 'admin/revenue_dashboard.html', context)


def custom_404(request, exception):
    """
    Custom 404 error page
    """
    return render(request, '404.html', status=404)


def custom_500(request):
    """
    Custom 500 error page
    """
    return render(request, '500.html', status=500)