#!/usr/bin/env python
import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'affiliate.settings')
django.setup()

from django.conf import settings

# Test API call
api_url = "https://www.cpagrip.com/common/offer_feed_json.php"
params = {
    'user_id': "2503693",
    'key': "655da6911e93776a7d5fc6fc1f1ea46e",
}

print("Testing CPAGrip API...")
print(f"URL: {api_url}")
print(f"Params: {params}")
print("-" * 80)

try:
    response = requests.get(api_url, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Type: {type(data)}")
        print(f"Total items: {len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 'N/A'}")
        print("-" * 80)
        
        # Pretty print the first few items
        if isinstance(data, list) and len(data) > 0:
            print(f"First offer details:")
            print(json.dumps(data[0], indent=2))
        elif isinstance(data, dict):
            if 'offers' in data:
                print(f"First offer details:")
                print(json.dumps(data['offers'][0], indent=2) if len(data['offers']) > 0 else "No offers")
            elif 'data' in data:
                print(f"First offer details:")
                print(json.dumps(data['data'][0], indent=2) if len(data['data']) > 0 else "No data")
            else:
                print("Data keys:", list(data.keys())[:5])
                if len(data) > 0:
                    first_key = list(data.keys())[0]
                    print(f"First item ({first_key}):")
                    print(json.dumps(data[first_key], indent=2))
        
        print("-" * 80)
        print("All offer names:")
        offers = []
        if isinstance(data, list):
            offers = data
        elif isinstance(data, dict):
            if 'offers' in data:
                offers = data['offers']
            elif 'data' in data:
                offers = data['data']
            else:
                offers = list(data.values())
        
        for i, offer in enumerate(offers[:10], 1):
            # Try to find the name field
            name = offer.get('name') or offer.get('title') or offer.get('offer_name') or 'Unknown'
            payout = offer.get('payout') or offer.get('amount') or offer.get('Payout') or 'Unknown'
            offer_type = offer.get('type') or offer.get('offer_type') or offer.get('category') or 'Unknown'
            countries = offer.get('countries') or offer.get('country') or 'Unknown'
            print(f"{i}. {name}")
            print(f"   Payout: ${payout}")
            print(f"   Type: {offer_type}")
            print(f"   Countries: {countries}")
            print()
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()