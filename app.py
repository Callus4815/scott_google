#!/usr/bin/env python3
"""
Flask API for Google Places Search
Provides REST API endpoints for the Vue.js frontend
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests
import json
import csv
import os
import tempfile
from typing import List, Dict, Any
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for Vue.js frontend

# Configuration
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

def search_places(text_query: str, page_token: str = None) -> Dict[str, Any]:
    """
    Search for places using Google Places API (New)
    
    Args:
        text_query: The search query text
        page_token: Optional page token for pagination
        
    Returns:
        JSON response from the API
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "*"
    }
    
    payload = {
        "textQuery": text_query
    }
    
    # Add page token if provided
    if page_token:
        payload["pageToken"] = page_token

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")

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

# Store for session data (in production, use Redis or database)
session_data = {}

@app.route('/api/search', methods=['POST'])
def search():
    """Initial search endpoint"""
    try:
        data = request.get_json()
        search_query = data.get('query', '').strip()
        
        if not search_query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Make initial API request
        api_response = search_places(search_query)
        places_data = extract_place_data(api_response)
        
        if not places_data:
            return jsonify({'error': 'No places found matching your search criteria'}), 404
        
        # Store session data
        session_id = f"session_{len(session_data)}"
        session_data[session_id] = {
            'query': search_query,
            'all_places': places_data,
            'next_page_token': api_response.get("nextPageToken"),
            'page_count': 1,
            'filename': generate_filename(search_query)
        }
        
        return jsonify({
            'session_id': session_id,
            'places': places_data,
            'has_more': bool(api_response.get("nextPageToken")),
            'total_count': len(places_data),
            'filename': session_data[session_id]['filename']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/more', methods=['POST'])
def search_more():
    """Get more results endpoint"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in session_data:
            return jsonify({'error': 'Invalid session'}), 400
        
        session = session_data[session_id]
        
        if not session['next_page_token']:
            return jsonify({'error': 'No more results available'}), 400
        
        if session['page_count'] >= 3:
            return jsonify({'error': 'Maximum results limit reached (60 results)'}), 400
        
        # Wait for token to become valid
        time.sleep(3)
        
        # Make additional API request
        api_response = search_places(session['query'], session['next_page_token'])
        additional_places = extract_place_data(api_response)
        
        if additional_places:
            # Add to session data
            session['all_places'].extend(additional_places)
            session['next_page_token'] = api_response.get("nextPageToken")
            session['page_count'] += 1
            
            return jsonify({
                'places': additional_places,
                'has_more': bool(api_response.get("nextPageToken")) and session['page_count'] < 3,
                'total_count': len(session['all_places']),
                'page_count': session['page_count']
            })
        else:
            return jsonify({'error': 'No additional places found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<session_id>')
def download_csv(session_id):
    """Download CSV file endpoint"""
    try:
        if session_id not in session_data:
            return jsonify({'error': 'Invalid session'}), 400
        
        session = session_data[session_id]
        places_data = session['all_places']
        filename = session['filename']
        
        if not places_data:
            return jsonify({'error': 'No data to download'}), 400
        
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        
        fieldnames = ["id", "displayName", "formattedAddress", "primaryType", "rating", "userRatingCount", "businessStatus"]
        
        with temp_file as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(places_data)
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
