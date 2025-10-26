#!/usr/bin/env python3
"""
Quick test script for Google Places API
Saves response JSON to a file for inspection
"""

import requests
import json
import os
from datetime import datetime

def test_places_api():
    """Test the Google Places API and save response to file"""
    
    # Get API key from environment variable
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Set it with: export GOOGLE_API_KEY='your_api_key_here'")
        return
    
    # Get search query from user input
    print("Enter your search query (e.g., 'restaurants in New York', 'HVAC contractors in Chicago'):")
    search_query = input("Search query: ").strip()
    
    if not search_query:
        print("No search query entered. Using default: 'restaurants in New York'")
        search_query = "restaurants in New York"
    
    # API endpoint
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "*"
    }
    
    payload = {
        "textQuery": search_query
    }
    
    print(f"Testing Google Places API...")
    print(f"Search query: {search_query}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print("Making request...")
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Get the JSON response
        data = response.json()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"places_api_test_{timestamp}.json"
        
        # Prepare complete log data including request details
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "url": url,
                "method": "POST",
                "headers": headers,
                "payload": payload,
                "search_query": search_query
            },
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": data
            }
        }
        
        # Save complete log to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Success! Response saved to: {filename}")
        print(f"Status Code: {response.status_code}")
        print(f"Response size: {len(json.dumps(data))} characters")
        
        # Show basic info about the response
        if 'places' in data:
            print(f"Number of places found: {len(data['places'])}")
            if data['places']:
                print(f"First place: {data['places'][0].get('displayName', {}).get('text', 'N/A')}")
        
        if 'nextPageToken' in data:
            print(f"Has next page token: Yes")
        else:
            print(f"Has next page token: No")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_places_api()
