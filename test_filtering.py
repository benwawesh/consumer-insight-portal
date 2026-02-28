#!/usr/bin/env python
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'affiliate.settings')
django.setup()

from django.conf import settings
from decimal import Decimal

print("=" * 80)
print("TESTING OFFER FILTERING LOGIC")
print("=" * 80)

# Show current settings
print(f"\nCurrent Settings:")
print(f"  MIN_PAYOUT_THRESHOLD: ${settings.MIN_PAYOUT_THRESHOLD}")
print(f"  ALLOWED_COUNTRIES: {settings.ALLOWED_COUNTRIES}")
print(f"  OFFER_TYPES: {settings.OFFER_TYPES}")

# Fetch offers from API
api_url = "https://www.cpagrip.com/common/offer_feed_json.php"
params = {
    'user_id': "2503693",
    'key': "655da6911e93776a7d5fc6fc1f1ea46e",
}

print(f"\nFetching offers from API...")
response = requests.get(api_url, params=params, timeout=30)
data = response.json()

# Convert to list
offers = []
for offer_id, offer_data in data.items():
    if isinstance(offer_data, dict):
        offer_data['offer_id'] = offer_id
        offers.append(offer_data)

print(f"Fetched {len(offers)} offers\n")
print("=" * 80)
print("TESTING EACH OFFER")
print("=" * 80)

# Test each offer
for i, offer in enumerate(offers, 1):
    print(f"\n{i}. {offer.get('title', 'Unknown')}")
    print(f"   Raw data: {offer}")
    
    # Extract fields
    offer_id = offer.get('offer_id')
    name = offer.get('title')
    payout = offer.get('payout')
    offer_type = offer.get('category')
    countries = offer.get('accepted_countries')
    
    print(f"\n   Extracted fields:")
    print(f"     ID: {offer_id}")
    print(f"     Name: {name}")
    print(f"     Payout: ${payout}")
    print(f"     Type: {offer_type}")
    print(f"     Countries: {countries}")
    
    # Test payout
    try:
        payout_decimal = Decimal(str(payout))
        payout_passes = payout_decimal >= settings.MIN_PAYOUT_THRESHOLD
        print(f"\n   Payout Check:")
        print(f"     Offer payout: ${payout}")
        print(f"     Threshold: ${settings.MIN_PAYOUT_THRESHOLD}")
        print(f"     Result: {'✓ PASS' if payout_passes else '✗ FAIL'}")
    except Exception as e:
        print(f"   Payout Check: ✗ ERROR - {e}")
        payout_passes = False
    
    # Test country
    country_passes = False
    if countries:
        countries_upper = countries.upper()
        for allowed_country in settings.ALLOWED_COUNTRIES:
            if allowed_country in countries_upper:
                country_passes = True
                break
    
    print(f"\n   Country Check:")
    print(f"     Offer countries: {countries}")
    print(f"     Allowed countries: {settings.ALLOWED_COUNTRIES}")
    print(f"     Result: {'✓ PASS' if country_passes else '✗ FAIL'}")
    
    # Test type
    type_passes = False
    if offer_type:
        offer_type_lower = offer_type.lower()
        for allowed_type in settings.OFFER_TYPES:
            if allowed_type.lower() in offer_type_lower:
                type_passes = True
                break
    
    print(f"\n   Type Check:")
    print(f"     Offer type: {offer_type}")
    print(f"     Allowed types: {settings.OFFER_TYPES}")
    print(f"     Result: {'✓ PASS' if type_passes else '✗ FAIL'}")
    
    # Overall result
    overall_passes = payout_passes and country_passes and type_passes
    print(f"\n   Overall Result: {'✓ PASS - Would be imported!' if overall_passes else '✗ FAIL - Would be filtered out'}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)