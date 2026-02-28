#!/usr/bin/env python
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'affiliate.settings')
django.setup()

from insights.services import CPAGripAPIService
from django.conf import settings

print("=" * 80)
print("DEBUGGING SYNC FUNCTION")
print("=" * 80)

# Show settings
print(f"\nSettings:")
print(f"  MIN_PAYOUT_THRESHOLD: ${settings.MIN_PAYOUT_THRESHOLD}")
print(f"  ALLOWED_COUNTRIES: {settings.ALLOWED_COUNTRIES}")
print(f"  OFFER_TYPES: {settings.OFFER_TYPES}")

# Create service instance
service = CPAGripAPIService()

# Fetch offers
print(f"\nFetching offers...")
offers = service.fetch_offers()
print(f"Fetched {len(offers)} offers")

if offers:
    print(f"\nFirst offer raw data:")
    print(offers[0])
    
    # Extract data
    offer_data = service._extract_offer_data(offers[0])
    print(f"\nExtracted data:")
    print(offer_data)
    
    # Test filtering
    print(f"\nFiltering offers...")
    filtered = service.filter_offers(offers)
    print(f"Filtered to {len(filtered)} offers")
    
    if filtered:
        print(f"\nFiltered offers:")
        for offer in filtered:
            print(f"  - {offer.get('name')}: ${offer.get('payout')}")