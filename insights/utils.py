import uuid
import logging
from django.conf import settings
from ipaddress import ip_address, AddressValueError
from django.utils import timezone

logger = logging.getLogger('insights')


def generate_tracking_id():
    """
    Generate a unique tracking ID using UUID4
    """
    return str(uuid.uuid4())


def detect_device_type(user_agent):
    """
    Detect device type from user agent string
    Returns: 'mobile', 'tablet', or 'desktop'
    """
    if not user_agent:
        return 'unknown'
    
    ua = user_agent.lower()
    
    # Tablet patterns (check these first as some tablets also match mobile)
    tablet_patterns = ['ipad', 'kindle', 'tablet', 'playbook']
    for pattern in tablet_patterns:
        if pattern in ua:
            return 'tablet'
    
    # Mobile patterns
    mobile_patterns = [
        'mobile', 'android', 'iphone', 'blackberry', 
        'opera mini', 'windows phone', 'palm', 'webos'
    ]
    for pattern in mobile_patterns:
        if pattern in ua:
            return 'mobile'
    
    # Default to desktop
    return 'desktop'


def detect_bot(user_agent):
    """
    Detect if user agent is likely a bot
    Returns: True if bot detected, False otherwise
    """
    if not user_agent:
        return True  # No user agent is suspicious
    
    ua = user_agent.lower()
    
    # Common bot patterns
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 
        'curl', 'wget', 'python-requests', 'headless',
        'phantom', 'selenium', 'puppeteer', 'cheerio',
        'googlebot', 'bingbot', 'slurp', 'duckduckbot',
        'baiduspider', 'yandexbot', 'ahrefsbot', 'mj12bot',
        'semrushbot', 'dotbot', 'ahrefsbot', 'hubspot',
        'monitor', 'scan', 'harvest', 'extract'
    ]
    
    for pattern in bot_patterns:
        if pattern in ua:
            return True
    
    return False


def get_client_ip(request):
    """
    Get the client's IP address from the request
    Handles proxies and load balancers
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


def is_valid_ip(ip_str):
    """
    Validate IP address format
    """
    try:
        ip_address(ip_str)
        return True
    except AddressValueError:
        return False


def get_user_agent(request):
    """
    Get the user agent from the request
    """
    return request.META.get('HTTP_USER_AGENT', '')


def get_referrer(request):
    """
    Get the referrer from the request
    """
    return request.META.get('HTTP_REFERER', '')


def append_tracking_id_to_url(url, tracking_id):
    """
    Append tracking_id to offer URL
    Handles URLs with existing query parameters
    """
    if not url:
        return url
    
    tracking_param = f'tracking_id={tracking_id}'
    
    if '?' in url:
        # URL already has query parameters
        separator = '&' if not url.endswith('&') else ''
        return f"{url}{separator}{tracking_param}"
    else:
        # URL has no query parameters
        return f"{url}?{tracking_param}"


def calculate_epc(total_revenue, total_conversions):
    """
    Calculate Earnings Per Click (EPC)
    Returns 0 if no conversions to avoid division by zero
    """
    if total_conversions and total_conversions > 0:
        return total_revenue / total_conversions
    return 0


def format_currency(amount):
    """
    Format currency amount with dollar sign and 2 decimal places
    """
    return f"${float(amount):.2f}"


def log_conversion_event(event_type, tracking_id, details=None):
    """
    Log conversion events for debugging and monitoring
    """
    message = f"Conversion Event: {event_type} - Tracking ID: {tracking_id}"
    if details:
        message += f" - Details: {details}"
    
    logger.info(message)


def get_time_ago(timestamp):
    """
    Get human-readable time ago string
    """
    if not timestamp:
        return 'N/A'
    
    now = timezone.now()
    diff = now - timestamp
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def is_us_ip(ip_str):
    """
    Check if IP address is from the US (simple check - not GeoIP)
    Note: This is a placeholder. For production, use a GeoIP database
    """
    # This is a simplified check. In production, use django-geoip2
    # or another GeoIP service for accurate country detection
    return True  # Placeholder - implement actual GeoIP check