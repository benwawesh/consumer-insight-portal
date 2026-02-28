import requests
import logging
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import CachedOffer
from .utils import append_tracking_id_to_url, log_conversion_event

logger = logging.getLogger('insights')


class CPAGripAPIService:
    """
    Service for interacting with CPAGrip API
    """
    
    def __init__(self):
        self.api_url = "https://www.cpagrip.com/common/offer_feed_json.php"
        self.user_id = "2503693"
        self.private_key = "655da6911e93776a7d5fc6fc1f1ea46e"
        self.min_payout = settings.MIN_PAYOUT_THRESHOLD
        self.allowed_countries = settings.ALLOWED_COUNTRIES
        self.offer_types = settings.OFFER_TYPES
        self.use_country_filter = getattr(settings, 'USE_COUNTRY_FILTER', False)
    
    def fetch_offers(self):
        """
        Fetch offers from CPAGrip API using country=0 to get all offers at once.

        Returns: List of offer dictionaries or None if failed
        """
        all_offers = {}

        params = {
            'user_id': self.user_id,
            'key': self.private_key,
            'country': '0',
        }

        try:
            response = requests.get(
                self.api_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict) and 'offers' in data:
                for offer in data['offers']:
                    offer_id = offer.get('offer_id')
                    if offer_id and offer_id not in all_offers:
                        all_offers[offer_id] = offer
                logger.info(f"Fetched {len(all_offers)} unique offers from CPAGrip")

        except Exception as e:
            logger.error(f"Failed to fetch offers: {e}")
            return None

        if not all_offers:
            logger.error("No offers returned from CPAGrip API")
            return None

        # Convert dict values to list
        offers_list = list(all_offers.values())
        logger.info(f"Fetched {len(offers_list)} total unique offers from CPAGrip across all countries")
        return offers_list
    
    def filter_offers(self, offers):
        """
        Filter offers based on criteria (optional country filtering)
        Returns: List of filtered offer dictionaries
        """
        filtered = []
        
        for offer in offers:
            try:
                # Extract offer data (handle different API response formats)
                offer_data = self._extract_offer_data(offer)
                if not offer_data:
                    continue
                
                # Check payout threshold
                payout = Decimal(str(offer_data.get('payout', 0)))
                if payout < self.min_payout:
                    continue
                
                # Optional country filtering (can be disabled via settings)
                if self.use_country_filter:
                    countries = offer_data.get('countries', '')
                    if not self._is_allowed_country(countries):
                        continue
                
                # Optional offer type filtering
                if self.offer_types:
                    offer_type = offer_data.get('type', '')
                    if offer_type and not self._is_allowed_type(offer_type):
                        continue
                
                filtered.append(offer_data)
                
            except Exception as e:
                logger.error(f"Error filtering offer: {e}")
                continue
        
        logger.info(f"Filtered to {len(filtered)} qualifying offers (out of {len(offers)} total)")
        return filtered
    
    def _extract_offer_data(self, offer):
        """
        Extract offer data from various API response formats
        Returns: Dictionary with standardized offer data or None
        """
        # Try common field names - priority order based on actual API response
        possible_fields = {
            'id': ['offer_id', 'id', 'OfferID', 'campaign_id'],
            'name': ['title', 'name', 'offer_name', 'Name', 'campaign_name'],
            'payout': ['payout', 'Payout', 'amount', 'payout_usd', 'earnings', 'price'],
            'link': ['offerlink', 'link', 'url', 'OfferLink', 'campaign_url'],
            'description': ['description', 'desc', 'Description'],
            'type': ['category', 'type', 'offer_type', 'Type'],
            'countries': ['accepted_countries', 'countries', 'country', 'Countries'],
            'offer_image': ['offerphoto', 'offer_photo', 'image', 'thumbnail', 'offer_image'],
            'net_epc': ['netepc', 'net_epc', 'epc', 'EPC'],
            'conversion_rate': ['conversion_rate', 'conversionrate', 'conversion_rate_percent'],
            'performance_percentage': ['performance', 'performance_percentage', 'perf_score'],
            'offer_category': ['category', 'offer_category', 'category_type'],
            'required_device': ['device', 'device_type', 'required_device', 'platform'],
            'clicks': ['clicks', 'total_clicks', 'click_count'],
            'leads': ['leads', 'conversions', 'total_leads', 'lead_count'],
        }
        
        extracted = {}
        
        for standard_field, possible_names in possible_fields.items():
            for name in possible_names:
                if name in offer:
                    extracted[standard_field] = offer[name]
                    break
        
        # Require essential fields
        if not all(key in extracted for key in ['id', 'name', 'payout', 'link']):
            return None
        
        return extracted
    
    def _is_allowed_country(self, countries):
        """
        Check if offer is allowed in configured countries
        """
        if not countries:
            return False
        
        countries_upper = countries.upper()
        for allowed_country in self.allowed_countries:
            if allowed_country in countries_upper:
                return True
        
        return False
    
    def _is_allowed_type(self, offer_type):
        """
        Check if offer type matches allowed types
        """
        if not offer_type:
            return False
        
        offer_type_lower = offer_type.lower()
        for allowed_type in self.offer_types:
            if allowed_type.lower() in offer_type_lower:
                return True
        
        return False
    
    def cache_offers(self, offers, status='pending'):
        """
        Cache offers in database with all metadata
        Updates existing offers or creates new ones
        
        Returns: Number of offers cached
        """
        cached_count = 0
        
        for offer in offers:
            try:
                offer_id = offer['id']
                
                # Prepare defaults with all fields
                defaults = {
                    'name': offer['name'][:200],
                    'description': offer.get('description', '')[:500],
                    'payout': Decimal(str(offer['payout'])),
                    'offer_link': offer['link'][:500],
                    'offer_type': offer.get('type', 'Unknown')[:50],
                    'countries': offer.get('countries', '')[:200],
                    'status': status,
                    # CPAGrip Dashboard fields
                    'offer_image': offer.get('offer_image', '')[:500],
                    'net_epc': Decimal(str(offer.get('net_epc', 0))),
                    'conversion_rate': Decimal(str(offer.get('conversion_rate', 0))),
                    'performance_percentage': int(offer.get('performance_percentage', 0)),
                    'offer_category': offer.get('offer_category', '')[:100],
                    'required_device': offer.get('required_device', '')[:50],
                    'clicks': int(offer.get('clicks', 0)),
                    'leads': int(offer.get('leads', 0)),
                    'date_added': offer.get('date_added'),
                }
                
                # Check if offer already exists
                cached_offer, created = CachedOffer.objects.update_or_create(
                    offer_id=offer_id,
                    defaults=defaults
                )
                
                if created:
                    logger.info(f"Cached new offer: {cached_offer.name}")
                else:
                    logger.info(f"Updated existing offer: {cached_offer.name}")
                
                cached_count += 1
                
            except Exception as e:
                logger.error(f"Error caching offer {offer.get('id', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return cached_count
    
    def get_random_live_offer(self):
        """
        Get a random live offer from the database
        
        Returns: CachedOffer object or None
        """
        try:
            live_offers = CachedOffer.objects.filter(status='live')
            
            if not live_offers.exists():
                logger.warning("No live offers available")
                return None
            
            # Prioritize featured offers
            featured_offers = live_offers.filter(is_featured=True)
            if featured_offers.exists():
                return featured_offers.order_by('display_order', '-payout').first()
            
            # Return highest payout non-featured offer
            return live_offers.order_by('-payout').first()
            
        except Exception as e:
            logger.error(f"Error getting random live offer: {e}")
            return None
    
    def get_offer_by_id(self, offer_id):
        """
        Get a specific offer by ID
        
        Returns: CachedOffer object or None
        """
        try:
            return CachedOffer.objects.get(offer_id=offer_id, status='live')
        except CachedOffer.DoesNotExist:
            logger.warning(f"Offer not found or not live: {offer_id}")
            return None
    
    def get_all_live_offers(self):
        """
        Get all live offers, sorted by featured status, display order, and payout
        
        Returns: QuerySet of CachedOffer objects
        """
        return CachedOffer.objects.filter(status='live').order_by(
            '-is_featured', 'display_order', '-payout'
        )


def fetch_and_cache_offers(status='pending'):
    """
    Convenience function to fetch, filter, and cache offers
    
    Returns: Number of offers cached or None if failed
    """
    service = CPAGripAPIService()
    
    # Fetch offers
    offers = service.fetch_offers()
    if offers is None:
        return None
    
    # Filter offers
    filtered_offers = service.filter_offers(offers)
    if not filtered_offers:
        logger.warning("No offers matched filtering criteria")
        return 0
    
    # Cache offers
    return service.cache_offers(filtered_offers, status=status)


def get_offer_with_tracking(tracking_id):
    """
    Get a live offer with tracking ID appended to the link
    
    Returns: CachedOffer object with modified offer_link or None
    """
    service = CPAGripAPIService()
    offer = service.get_random_live_offer()
    
    if offer:
        # Append tracking ID to offer link
        offer.offer_link = append_tracking_id_to_url(offer.offer_link, tracking_id)
    
    return offer


def get_offer_by_id_with_tracking(offer_id, tracking_id):
    """
    Get a specific offer by ID with tracking ID appended to the link
    
    Returns: CachedOffer object with modified offer_link or None
    """
    service = CPAGripAPIService()
    offer = service.get_offer_by_id(offer_id)
    
    if offer:
        # Append tracking ID to offer link
        offer.offer_link = append_tracking_id_to_url(offer.offer_link, tracking_id)
    
    return offer
