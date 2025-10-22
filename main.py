#!/usr/bin/env python3
"""
Google Places API Text Search Script
Converts curl command to Python requests and outputs results to CSV
"""

import requests
import json
import csv
import sys
import time
from typing import List, Dict, Any


def search_places(text_query: str, api_key: str, page_token: str = None) -> Dict[str, Any]:
    """
    Search for places using Google Places API (New)
    
    Args:
        text_query: The search query text
        api_key: Google API key
        page_token: Optional page token for pagination
        
    Returns:
        JSON response from the API
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "*"
    }
    
    payload = {
        "textQuery": text_query
    }
    
    # Add page token if provided
    if page_token:
        payload["pageToken"] = page_token

    try:
        print(f"Payload: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        sys.exit(1)


def extract_place_data(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant data from API response
    
    Args:
        api_response: Raw API response
        
    Returns:
        List of dictionaries containing place data
    """
    places_data = []
    
    if "places" not in api_response:
        print("No places found in API response")
        return places_data
    
    for place in api_response["places"]:
        place_data = {
            "id": place.get("id", ""),
            "displayName": place.get("displayName", {}).get("text", ""),
            "formattedAddress": place.get("formattedAddress", ""),
            "primaryType": place.get("primaryType", ""),
            "rating": place.get("rating", ""),
            "userRatingCount": place.get("userRatingCount", ""),
            "businessStatus": place.get("businessStatus", "")
        }
        places_data.append(place_data)
    
    return places_data


def save_to_csv(places_data: List[Dict[str, Any]], filename: str = "places_results.csv", append: bool = False) -> None:
    """
    Save places data to CSV file
    
    Args:
        places_data: List of place dictionaries
        filename: Output CSV filename
        append: Whether to append to existing file (True) or overwrite (False)
    """
    if not places_data:
        print("No data to save to CSV")
        return
    
    fieldnames = ["id", "displayName", "formattedAddress", "primaryType", "rating", "userRatingCount", "businessStatus"]
    
    try:
        mode = 'a' if append else 'w'
        with open(filename, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Only write header if not appending or if file is empty
            if not append or csvfile.tell() == 0:
                writer.writeheader()
            
            writer.writerows(places_data)
        
        action = "appended to" if append else "saved to"
        print(f"Results {action} {filename}")
        print(f"Added {len(places_data)} places")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")
        sys.exit(1)


def ask_user_for_more_results() -> bool:
    """
    Ask user if they want to gather more results
    
    Returns:
        True if user wants more results, False otherwise
    """
    while True:
        response = input("\nWould you like to gather more results? (Y/N): ").strip().upper()
        if response in ['Y', 'YES']:
            return True
        elif response in ['N', 'NO']:
            return False
        else:
            print("Please enter Y or N")


def get_user_search_query() -> str:
    """
    Get search query from user input
    
    Returns:
        User-entered search query string
    """
    while True:
        search_query = input("\nEnter your search query (e.g., 'HVAC contractor in Fuquay-Varina North Carolina'): ").strip()
        if search_query:
            return search_query
        else:
            print("Please enter a valid search query.")


def generate_filename(search_query: str) -> str:
    """
    Generate filename from search query
    
    Args:
        search_query: The search query string
        
    Returns:
        Generated filename string
    """
    import re
    
    # Extract city/location (look for "in [location]" pattern)
    city_match = re.search(r'in\s+([^,]+)', search_query, re.IGNORECASE)
    if city_match:
        city = city_match.group(1).strip()
    else:
        # If no "in" pattern, try to extract last part as location
        parts = search_query.split()
        if len(parts) > 2:
            city = parts[-2] + "_" + parts[-1]  # Last two words as city
        else:
            city = "search_results"
    
    # Extract business type (first part before "in")
    business_type = search_query.split(' in ')[0].strip() if ' in ' in search_query.lower() else search_query.split()[0]
    
    # Clean up the strings for filename
    city = re.sub(r'[^\w\s-]', '', city).strip()
    city = re.sub(r'[-\s]+', '_', city)
    
    business_type = re.sub(r'[^\w\s-]', '', business_type).strip()
    business_type = re.sub(r'[-\s]+', '_', business_type)
    
    # Generate filename
    filename = f"{city}_{business_type}_results.csv"
    
    return filename


def main():
    """Main function to execute the places search and CSV export"""
    
    # Configuration
    API_KEY = "AIzaSyAVR12_g2-vHAT3nE4lzSaA3996cc_01EI"
    
    # Get search query from user
    SEARCH_QUERY = get_user_search_query()
    
    # Generate filename from search query
    filename = generate_filename(SEARCH_QUERY)
    
    print(f"\nSearching for: {SEARCH_QUERY}")
    print(f"Results will be saved to: {filename}")
    print("Making API request...")
    
    # Make initial API request
    api_response = search_places(SEARCH_QUERY, API_KEY)
    
    # Extract data from first response
    all_places_data = extract_place_data(api_response)
    
    if not all_places_data:
        print("No places found matching your search criteria")
        return
    
    # Save initial results to CSV
    save_to_csv(all_places_data, filename)
    
    # Check for nextPageToken and ask user if they want more results
    next_page_token = api_response.get("nextPageToken")
    
    page_count = 1
    max_pages = 3  # Google Places API limit is typically 60 results (3 pages × 20 results)
    
    while next_page_token and page_count < max_pages:
        if ask_user_for_more_results():
            print(f"\nFetching page {page_count + 1} of results...")
            print("Waiting for next page token to become valid (3 seconds)...")
            time.sleep(3)  # Required delay for nextPageToken to become valid
            
            print("Making additional API request...")
            
            # Make additional API request with page token
            additional_response = search_places(SEARCH_QUERY, API_KEY, next_page_token)
            
            # Extract data from additional response
            additional_places_data = extract_place_data(additional_response)
            
            if additional_places_data:
                # Append to CSV
                save_to_csv(additional_places_data, filename, append=True)
                
                # Add to our running total
                all_places_data.extend(additional_places_data)
                
                # Get next page token for potential continuation
                next_page_token = additional_response.get("nextPageToken")
                page_count += 1
            else:
                print("No additional places found")
                next_page_token = None
        else:
            break
    
    if page_count >= max_pages:
        print(f"\nReached maximum limit of {max_pages * 20} results (3 pages)")
    
    # Display final summary
    print(f"\nFinal Summary:")
    print(f"Total places found: {len(all_places_data)}")
    print("\nAll results:")
    for i, place in enumerate(all_places_data, 1):
        print(f"{i}. {place['displayName']} - {place['formattedAddress']}")


if __name__ == "__main__":
    main()
