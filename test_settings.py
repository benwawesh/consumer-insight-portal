#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'affiliate.settings')
django.setup()

from django.conf import settings

print("Testing Django Settings...")
print("-" * 80)
print(f"MIN_PAYOUT_THRESHOLD: ${settings.MIN_PAYOUT_THRESHOLD}")
print(f"ALLOWED_COUNTRIES: {settings.ALLOWED_COUNTRIES}")
print(f"OFFER_TYPES: {settings.OFFER_TYPES}")
print(f"Number of countries: {len(settings.ALLOWED_COUNTRIES)}")
print(f"Number of offer types: {len(settings.OFFER_TYPES)}")
print("-" * 80)

# Test filtering logic
from insights.services import CPAGripAPI

test_countries = ['KE', 'US', 'GB']
for country in test_countries:
    if country in settings.ALLOWED_COUNTRIES:
        print(f"✓ {country} is in ALLOWED_COUNTRIES")
    else:
        print(f"✗ {country} is NOT in ALLOWED_COUNTRIES")