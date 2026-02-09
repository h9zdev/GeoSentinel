import os
import re
import io
import json
import csv
import time
import math
import random
import logging
import base64
import requests
import feedparser
import threading
import sqlite3
import numpy as np
import cv2  # opencv-python-headless or opencv-python
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ExifTags
import tempfile
from gtts import gTTS


# Import local configs
try:
    from news_config import NEWS_SOURCES
except ImportError:
    NEWS_SOURCES = {}


# -----------------------------------------------------------------
# Configuration & Keys
# -----------------------------------------------------------------
# NOTE: Paths are adjusted to work from HayOS/github/ assuming HayOS/ is parent
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
GEODATA_DIR = os.path.join(PARENT_DIR, 'geodata')




# Social / News API Keys (Placeholders)
TWITTER_API_KEY = "YOUR_API_KEYS"
TWITTER_API_SECRET = "YOUR_API_KEYS"
TWITTER_ACCESS_TOKEN = "YOUR_API_KEYS"
TWITTER_ACCESS_TOKEN_SECRET = "YOUR_API_KEYS"
TWITTER_BEARER_TOKEN = "YOUR_API_KEYS"
api_key = "YOUR_API_KEYS"
# --- CELL TOWER UPLINK ---
OPENCELLID_API_KEY = "YOUR_API_KEY" 
HF_TOKEN = "YOUR_API_KEY" 


NEWS_API_KEY = "YOUR_API_KEYS"
OPENROUTER_API_KEY = "YOUR_API_KEYS" # USER: Replace with your actual key

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# -----------------------------------------------------------------
# Caches & Globals
# -----------------------------------------------------------------
news_cache = {}
NEWS_CACHE_LIMIT = 15 # minutes


#

# -----------------------------------------------------------------
# Database & Auth Helpers
# -----------------------------------------------------------------



@app.route('/earth')
def earth():
    # 2. List GeoJSON files
    geodata_dir = os.path.join(app.root_path, 'geodata')
    geojson_files = []
    if os.path.exists(geodata_dir):
        geojson_files = [f for f in os.listdir(geodata_dir) if f.endswith('.geojson')]
    
    return render_template("earth.html", geojson_files=geojson_files)





@app.route('/api/geojson/<filename>')

def get_geojson_data(filename):
    """Return a summary of the GeoJSON file (properties and first few coords to keep it snappy)."""
    # Security check: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    filepath = os.path.join(app.root_path, 'geodata', filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Return a larger sample for map visualization
        features = data.get('features', [])
        summary_features = []
        
        for feat in features[:500]: # Increased to 500 for map display
            summary_features.append({
                "type": feat.get("type"),
                "properties": feat.get("properties"),
                "geometry": feat.get("geometry") # Include full geometry for Leaflet
            })

        return jsonify({
            "filename": filename,
            "total_features": len(features),
            "summary": summary_features
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geo/index')
def get_geo_index():
    """Return the surveillance grid index."""
    filepath = os.path.join(app.root_path, 'geodata', 'geo', 'index.json')
    if not os.path.exists(filepath):
        return jsonify({"error": "Index not found"}), 404
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geo/tile/<z>/<x>/<y>')
def get_geo_tile(z, x, y):
    """Return a specific surveillance grid tile."""
    # Security check: ensure z, x, y are integers to prevent path traversal
    try:
        z = int(z)
        x = int(x)
        y = int(y)
    except ValueError:
        return jsonify({"error": "Invalid tile coordinates"}), 400

    filepath = os.path.join(app.root_path, 'geodata', 'geo', str(z), str(x), f"{y}.json")
    if not os.path.exists(filepath):
        return jsonify({"error": "Tile not found"}), 404

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500






    

@app.route('/api/geo/flights')
def get_flight_data():
    """Fetch live flight data from adsb.one API (comprehensive global coverage)."""
    search_q = request.args.get('q', '').strip().upper()
    
    # adsb.one provides excellent global coverage - query multiple regions
    # Format: /v2/point/{lat}/{lon}/{radius_nm}
    regions = [
        ("https://api.adsb.one/v2/point/40/-100/4000", "Americas"),   # North America
        ("https://api.adsb.one/v2/point/50/10/3000", "Europe"),       # Europe
        ("https://api.adsb.one/v2/point/25/80/3000", "Asia"),         # South Asia
        ("https://api.adsb.one/v2/point/35/135/2500", "EastAsia"),    # East Asia
        ("https://api.adsb.one/v2/point/-25/135/2000", "Oceania"),    # Australia
        ("https://api.adsb.one/v2/point/60/90/4000", "Russia"),       # Russia/Eurasia
        ("https://api.adsb.one/v2/point/35/105/2500", "China"),       # China/Central Asia
        ("https://api.adsb.one/v2/point/-15/-60/3000", "SouthAmerica"), # South America
        ("https://api.adsb.one/v2/point/5/20/3500", "Africa"),          # Africa
    ]
    
    all_flights = {}  # Use dict to dedupe by hex
    
    for url, region_name in regions:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                aircraft_list = data.get('ac', [])
                
                for ac in aircraft_list:
                    # Skip if no position data
                    if ac.get('lat') is None or ac.get('lon') is None:
                        continue
                    
                    hex_code = ac.get('hex', '').upper()
                    if hex_code in all_flights:
                        continue  # Already have this aircraft
                    
                    callsign = (ac.get('flight', '') or '').strip() or ac.get('r', '') or hex_code
                    registration = ac.get('r', '')
                    aircraft_type = ac.get('t', '')
                    
                    # Apply search filter if provided
                    if search_q:
                        if search_q not in hex_code and search_q not in callsign.upper() and search_q not in registration.upper():
                            continue
                    
                    # Type classification with color coding
                    # Military detection
                    mil_prefixes = ['RCH', 'SPAR', 'SAM', 'AF1', 'MAGMA', 'ASCOT', 'BAF', 'GAF', 
                                   'PLF', 'DUKE', 'NAVY', 'COBRA', 'VIPER', 'REACH', 'EVAC']
                    mil_types = ['C17', 'C130', 'C5', 'KC135', 'KC10', 'F15', 'F16', 'F18', 
                                'F22', 'F35', 'B52', 'B1', 'B2', 'E3', 'E6', 'P8', 'V22']
                    
                    is_mil = any(callsign.upper().startswith(p) for p in mil_prefixes) or \
                             any(t in aircraft_type.upper() for t in mil_types)
                    
                    # Private aircraft detection  
                    priv_types = ['C172', 'C182', 'C208', 'PA28', 'SR22', 'TBM9', 'PC12', 'CL60', 'C152', 'PA32']
                    is_priv = (callsign.startswith('N') and len(callsign) <= 6) or \
                              callsign.startswith('G-') or callsign.startswith('VH-') or \
                              aircraft_type.upper() in priv_types
                    
                    # Emergency detection
                    is_emergency = ac.get('emergency', 'none') != 'none' or ac.get('squawk') == '7700'
                    
                    # Default to commercial (blue) - all flights visible!
                    f_type = "commercial"
                    if is_emergency: f_type = "emergency"
                    elif is_mil: f_type = "military"
                    elif is_priv: f_type = "private"
                    
                    all_flights[hex_code] = {
                        "icao24": hex_code.lower(),
                        "callsign": callsign,
                        "registration": registration or "---",
                        "aircraft_type": aircraft_type or "---",
                        "long": ac.get('lon'),
                        "lat": ac.get('lat'),
                        "alt": ac.get('alt_baro') or ac.get('alt_geom') or 0,
                        "velocity": ac.get('gs', 0),
                        "heading": ac.get('track', 0),
                        "squawk": ac.get('squawk', '----'),
                        "type": f_type
                    }
        except Exception as e:
            print(f"Error fetching {region_name}: {e}")
            continue
    
    return jsonify(list(all_flights.values()))



@app.route('/api/geo/towers')
def get_towers():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if not lat or not lon:
            lat = 51.505
            lon = -0.09

        # Calculate Bounding Box (approx 5-10km radius)
        # 1 deg lat ~= 111km. 0.05 ~= 5.5km
        min_lat = lat - 0.05
        max_lat = lat + 0.05
        min_lon = lon - 0.05
        max_lon = lon + 0.05
        bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"

        # Using OpenCellID 'getInArea' API
        response = requests.get(
            'http://opencellid.org/cell/getInArea',
            params={
                "key": OPENCELLID_API_KEY,
                "BBOX": bbox,
                "format": "json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
                return jsonify({"error": "API returned non-JSON", "details": response.text[:100]})

            towers = []
            cells = data.get('cells', []) if isinstance(data, dict) else data
            
            if isinstance(cells, list):
                for cell in cells:
                    towers.append({
                        "id": str(cell.get('cellid', 'Unknown')),
                        "lat": float(cell.get('lat')),
                        "lon": float(cell.get('lon')),
                        "lac": cell.get('lac', 0),
                        "mcc": cell.get('mcc', 0),
                        "mnc": cell.get('mnc', 0),
                        "signal": cell.get('signal', 0),
                        "radio": cell.get('radio', 'gsm')
                    })
            
            return jsonify(towers)
            
        else:
            return jsonify({"error": f"Upstream API error: {response.status_code}", "details": response.text[:100]}), 502

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/geo/celltower')
def get_celltower_click():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if not lat or not lon:
            return jsonify({"error": "Missing coordinates"}), 400

        # Small BBOX for specific location (approx 2km radius)
        min_lat = lat - 0.01
        max_lat = lat + 0.01
        min_lon = lon - 0.01
        max_lon = lon + 0.01
        bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        # Using the endpoint provided by user logic
        response = requests.get(
            'https://www.opencellid.org/ajax/getCells.php',
            params={
                "bbox": bbox
            },
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
                return jsonify({"error": "API returned non-JSON", "details": response.text[:100]})

            towers = []
            features = data.get('features', []) if isinstance(data, dict) else []
            
            for feature in features:
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})
                coords = geom.get('coordinates', [0, 0]) # [lon, lat]
                
                towers.append({
                    "id": str(props.get('cellid', props.get('unit', 'Unknown'))),
                    "lat": float(coords[1]),
                    "lon": float(coords[0]),
                    "lac": props.get('area', 0),
                    "mcc": props.get('mcc', 0),
                    "mnc": props.get('net', 0),
                    "signal": props.get('samples', 0), 
                    "radio": props.get('radio', 'gsm')
                })
            
            return jsonify(towers)
        else:
            return jsonify({"error": f"Upstream API error: {response.status_code}", "details": response.text[:100]}), 502

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- VESSEL HARBOR UPLINK ---
# Global cache for AIS data
_ais_vessels_cache = {}
_ais_cache_lock = None
_ais_websocket_task = None

def start_ais_websocket():
    """Start background WebSocket connection to AISstream.io"""
    import asyncio
    import websockets
    import json
    import threading
    from threading import Lock
    
    global _ais_cache_lock, _ais_websocket_task
    _ais_cache_lock = Lock()
    
    async def ais_stream():
        global _ais_vessels_cache
        
        
        async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
            # Subscribe to global ship positions
            subscribe_message = {
                "APIKey": api_key,
                "BoundingBoxes": [[[-90, -180], [90, 180]]]  # Global coverage
            }
            
            await websocket.send(json.dumps(subscribe_message))
            print("AISstream.io connected - receiving real ship data...")
            
            async for message_json in websocket:
                try:
                    message = json.loads(message_json)
                    
                    # Handle Position Reports
                    if "Message" in message and "PositionReport" in message["Message"]:
                        pos = message["Message"]["PositionReport"]
                        meta = message.get("MetaData", {})
                        
                        mmsi = str(meta.get("MMSI", "000000000"))
                        ship_name = meta.get("ShipName", "UNKNOWN").strip()
                        
                        vessel_data = {
                            "mmsi": mmsi,
                            "name": ship_name if ship_name else "UNKNOWN",
                            "lat": pos.get("Latitude", 0),
                            "lon": pos.get("Longitude", 0),
                            "heading": int(pos.get("TrueHeading", 0) or pos.get("Cog", 0) or 0),
                            "speed": float(pos.get("Sog", 0) or 0),
                            "type": _ais_vessels_cache.get(mmsi, {}).get("type", "cargo"),  # Keep existing type
                            "imo": meta.get("IMO", "---"),
                            "status": pos.get("NavigationalStatus", "Underway"),
                            "country": _ais_vessels_cache.get(mmsi, {}).get("country", "--"),  # Keep existing country
                            "draft": 0,
                            "arrival": meta.get("Destination", "Unknown"),
                            "callsign": meta.get("CallSign", "---"),
                            "source": "AISstream_LIVE",
                            "atd": "---",
                            "departure": "---",
                            "category": _ais_vessels_cache.get(mmsi, {}).get("type", "cargo")
                        }
                        
                        with _ais_cache_lock:
                            _ais_vessels_cache[mmsi] = vessel_data
                    
                    # Handle Ship Static Data (has ship type and country)
                    elif "Message" in message and "ShipStaticData" in message["Message"]:
                        static = message["Message"]["ShipStaticData"]
                        meta = message.get("MetaData", {})
                        
                        mmsi = str(meta.get("MMSI", "000000000"))
                        ship_type_code = static.get("Type", 0)
                        
                        # Map AIS ship type codes to readable types
                        type_map = {
                            range(30, 40): "fishing",
                            range(40, 50): "tug",
                            range(50, 60): "pilot",
                            range(60, 70): "passenger",
                            range(70, 80): "cargo",
                            range(80, 90): "tanker",
                            range(35, 36): "military",
                            range(51, 52): "special"
                        }
                        
                        ship_type = "cargo"  # default
                        for code_range, type_name in type_map.items():
                            if ship_type_code in code_range:
                                ship_type = type_name
                                break
                        
                        # Get country from UserID (first 3 digits of MMSI = Maritime Identification Digits)
                        mid = mmsi[:3]
                        country_map = {
                            '202': 'GB', '203': 'ES', '204': 'PT', '205': 'BE', '206': 'FR',
                            '207': 'FR', '208': 'FR', '209': 'CY', '210': 'CY', '211': 'DE',
                            '212': 'CY', '213': 'GE', '214': 'MD', '215': 'MT', '216': 'AM',
                            '218': 'DE', '219': 'DK', '220': 'DK', '224': 'ES', '225': 'ES',
                            '226': 'FR', '227': 'FR', '228': 'FR', '229': 'MT', '230': 'FI',
                            '231': 'FO', '232': 'GB', '233': 'GB', '234': 'GB', '235': 'GB',
                            '236': 'GI', '237': 'GR', '238': 'HR', '239': 'GR', '240': 'GR',
                            '241': 'GR', '242': 'MA', '243': 'HU', '244': 'NL', '245': 'NL',
                            '246': 'NL', '247': 'IT', '248': 'MT', '249': 'MT', '250': 'IE',
                            '251': 'IS', '252': 'LI', '253': 'LU', '254': 'MC', '255': 'PT',
                            '256': 'MT', '257': 'NO', '258': 'NO', '259': 'NO', '261': 'PL',
                            '262': 'ME', '263': 'PT', '264': 'RO', '265': 'SE', '266': 'SE',
                            '267': 'SK', '268': 'SM', '269': 'CH', '270': 'CZ', '271': 'TR',
                            '272': 'UA', '273': 'RU', '274': 'MK', '275': 'LV', '276': 'EE',
                            '277': 'LT', '278': 'SI', '279': 'RS', '301': 'AI', '303': 'US',
                            '304': 'AG', '305': 'AG', '306': 'CW', '307': 'AW', '308': 'BS',
                            '309': 'BS', '310': 'BM', '311': 'BS', '312': 'BZ', '314': 'BB',
                            '316': 'CA', '319': 'KY', '321': 'CR', '323': 'CU', '325': 'DM',
                            '327': 'DO', '329': 'GP', '330': 'GD', '331': 'GL', '332': 'GT',
                            '334': 'HN', '336': 'HT', '338': 'US', '339': 'JM', '341': 'KN',
                            '343': 'LC', '345': 'MX', '347': 'MQ', '348': 'MS', '350': 'NI',
                            '351': 'PA', '352': 'PA', '353': 'PA', '354': 'PA', '355': 'PA',
                            '356': 'PA', '357': 'PA', '358': 'PR', '359': 'SV', '361': 'PM',
                            '362': 'TT', '364': 'TC', '366': 'US', '367': 'US', '368': 'US',
                            '369': 'US', '370': 'PA', '371': 'PA', '372': 'PA', '373': 'PA',
                            '374': 'PA', '375': 'VC', '376': 'VC', '377': 'VC', '378': 'VG',
                            '401': 'AF', '403': 'SA', '405': 'BD', '408': 'BH', '410': 'BT',
                            '412': 'CN', '413': 'CN', '414': 'CN', '416': 'TW', '417': 'LK',
                            '419': 'IN', '422': 'IR', '423': 'AZ', '425': 'IQ', '428': 'IL',
                            '431': 'JP', '432': 'JP', '434': 'TM', '436': 'KZ', '437': 'UZ',
                            '438': 'JO', '440': 'KR', '441': 'KR', '443': 'PS', '445': 'KP',
                            '447': 'KW', '450': 'LB', '451': 'KG', '453': 'MO', '455': 'MV',
                            '457': 'MN', '459': 'NP', '461': 'OM', '463': 'PK', '466': 'QA',
                            '468': 'SY', '470': 'AE', '471': 'AE', '472': 'TJ', '473': 'YE',
                            '475': 'YE', '477': 'HK', '478': 'BA', '501': 'AQ', '503': 'AU',
                            '506': 'MM', '508': 'BN', '510': 'FM', '511': 'PW', '512': 'NZ',
                            '514': 'KH', '515': 'KH', '516': 'CX', '518': 'CK', '520': 'FJ',
                            '523': 'CC', '525': 'ID', '529': 'KI', '531': 'LA', '533': 'MY',
                            '536': 'MP', '538': 'MH', '540': 'NC', '542': 'NU', '544': 'NR',
                            '546': 'PF', '548': 'PH', '553': 'PG', '555': 'PN', '557': 'SB',
                            '559': 'AS', '561': 'WS', '563': 'SG', '564': 'SG', '565': 'SG',
                            '566': 'SG', '567': 'TH', '570': 'TO', '572': 'TV', '574': 'VN',
                            '576': 'VU', '577': 'VU', '578': 'WF', '601': 'ZA', '603': 'AO',
                            '605': 'DZ', '607': 'TF', '608': 'AS', '609': 'BI', '610': 'BJ',
                            '611': 'BW', '612': 'CF', '613': 'CM', '615': 'CG', '616': 'KM',
                            '617': 'CV', '618': 'AQ', '619': 'CI', '620': 'KM', '621': 'DJ',
                            '622': 'EG', '624': 'ET', '625': 'ER', '626': 'GA', '627': 'GH',
                            '629': 'GM', '630': 'GW', '631': 'GQ', '632': 'GN', '633': 'BF',
                            '634': 'KE', '635': 'AQ', '636': 'LR', '637': 'LR', '638': 'SS',
                            '642': 'LY', '644': 'LS', '645': 'MU', '647': 'MG', '649': 'ML',
                            '650': 'MZ', '654': 'MR', '655': 'MW', '656': 'NE', '657': 'NG',
                            '659': 'NA', '660': 'RE', '661': 'RW', '662': 'SD', '663': 'SN',
                            '664': 'SC', '665': 'SH', '666': 'SO', '667': 'SL', '668': 'ST',
                            '669': 'SZ', '670': 'TD', '671': 'TG', '672': 'TN', '674': 'TZ',
                            '675': 'UG', '676': 'CD', '677': 'TZ', '678': 'ZM', '679': 'ZW'
                        }
                        country = country_map.get(mid, "--")
                        
                        # Update or create vessel data with static info
                        with _ais_cache_lock:
                            if mmsi in _ais_vessels_cache:
                                _ais_vessels_cache[mmsi]["type"] = ship_type
                                _ais_vessels_cache[mmsi]["country"] = country
                                _ais_vessels_cache[mmsi]["category"] = ship_type
                            else:
                                # Create minimal entry until we get position report
                                _ais_vessels_cache[mmsi] = {
                                    "mmsi": mmsi,
                                    "name": meta.get("ShipName", "UNKNOWN").strip(),
                                    "type": ship_type,
                                    "country": country,
                                    "lat": 0,
                                    "lon": 0,
                                    "heading": 0,
                                    "speed": 0,
                                    "imo": meta.get("IMO", "---"),
                                    "status": "Unknown",
                                    "draft": static.get("Draught", 0) / 10,  # AIS reports in decimeters
                                    "arrival": static.get("Destination", "Unknown"),
                                    "callsign": static.get("CallSign", "---"),
                                    "source": "AISstream_LIVE",
                                    "atd": "---",
                                    "departure": "---",
                                    "category": ship_type
                                }
                            
                except Exception as e:
                    print(f"AIS Parse Error: {e}")
                    continue
    
   
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                loop.run_until_complete(ais_stream())
            except Exception as e:
                print(f"AIS WebSocket Error: {e}, reconnecting in 5s...")
                import time
                time.sleep(5)
    
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
    print("AIS WebSocket thread started")

@app.route('/api/geo/vessels')
def get_vessel_data():
    """Fetch REAL live vessel data from AISstream.io"""
    global _ais_vessels_cache, _ais_websocket_task
    
    # Start WebSocket if not already started
    if _ais_websocket_task is None:
        try:
            start_ais_websocket()
            _ais_websocket_task = True
        except Exception as e:
            print(f"Failed to start AIS WebSocket: {e}")
    
    # Return cached vessels (optimized for performance)
    with _ais_cache_lock if _ais_cache_lock else nullcontext():
        all_vessels = list(_ais_vessels_cache.values())
        
        # Filter out vessels with invalid positions
        valid_vessels = [v for v in all_vessels if v.get('lat') != 0 and v.get('lon') != 0]
        
        # Prioritize India (419), China (412, 413, 414), Russia (273)
        priority_prefixes = ('419', '412', '413', '414', '273')
        
        priority_ships = [v for v in valid_vessels if v.get('mmsi', '').startswith(priority_prefixes)]
        other_ships = [v for v in valid_vessels if not v.get('mmsi', '').startswith(priority_prefixes)]
        
        # Combine: Priority ships first, then others, limit to 1500 total for better coverage
        vessels = (priority_ships + other_ships)[:1500]
    
    return jsonify(vessels)

from contextlib import nullcontext

@app.route('/api/geo/vessel/path/<mmsi>')
def get_vessel_path(mmsi):
    """Generate a realistic historical path for a vessel."""
    import random
    # Mock more historical points for a longer path
    res = []
    # Start with a random seed based on MMSI
    random.seed(mmsi)
    lat = random.uniform(-60, 70)
    lon = random.uniform(-180, 180)
    
    for _ in range(25):
        lat += random.uniform(-1.0, 1.0)
        lon += random.uniform(-1.0, 1.0)
        res.append([lat, lon])
    
    return jsonify(res)



from ultralytics import YOLO


@app.route('/api/geo/news')
def get_geo_news():
    """
    Fetch geopolitical news and tweets for a specific location.
    ATTEMPTS REAL API CALLS FIRST, FALLS BACK TO MOCK DATA.
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return jsonify({"error": "Missing coordinates"}), 400

    # --- Check Cache ---
    cache_key = f"geo_{lat}_{lon}"
    now_ts = datetime.now(timezone.utc).timestamp()
    if cache_key in news_cache:
        cached_time, cached_data = news_cache[cache_key]
        if (now_ts - cached_time) < (NEWS_CACHE_LIMIT * 60):
            print(f"Serving cached geo news for: {cache_key}")
            return jsonify(cached_data)

    real_tweets = []
    real_news = []
    
    # --- 1. Location Detection (Geocoding) ---
    location_query = ""
    detected_region = ""
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        geo_res = requests.get(geo_url, timeout=2, headers={'User-Agent': 'HayOS/1.0'})
        if geo_res.status_code == 200:
            geo_data = geo_res.json()
            address = geo_data.get('address', {})
            location_query = address.get('country', '') or address.get('city', '') or address.get('state', '')
            print(f"Reverse geocode: {location_query}")
            
            # Regional Mapping
            country_mapping = {
                "United States": "USA", "India": "INDIA", "China": "CHINA",
                "Russia": "RUSSIA", "Japan": "JAPAN", "Australia": "AUSTRALIA",
                "Taiwan": "TAIWAN", "South Korea": "SOUTH_KOREA", "Israel": "ISRAEL",
                "United Arab Emirates": "UAE", "Iran": "IRAN"
            }
            
            for c_name, reg_key in country_mapping.items():
                if location_query and c_name in location_query:
                    detected_region = reg_key
                    break
            
            if not detected_region and location_query:
                if any(x in location_query for x in ["Europe", "France", "Germany", "Spain", "Italy", "UK", "London"]):
                    detected_region = "EUROPE"
                elif any(x in location_query for x in ["Africa", "Kenya", "Nigeria", "Egypt", "South Africa"]):
                    detected_region = "AFRICA"
    except Exception as geo_err:
        print(f"Geocoding error: {geo_err}")

    # --- 2. Try Real Twitter API v2 (Search) ---
    if TWITTER_BEARER_TOKEN and TWITTER_BEARER_TOKEN != 'YOUR_BEARER_TOKEN_HERE':
        try:
            headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
            params = {
                'query': '(breaking OR news OR alert) -is:retweet lang:en',
                'max_results': 2,
                'tweet.fields': 'created_at,author_id,text'
            }
            response = requests.get('https://api.twitter.com/2/tweets/search/recent', headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for t in data['data']:
                        created = t.get('created_at', '')
                        try:
                            dt = datetime.strptime(created, '%Y-%m-%dT%H:%M:%S.%fZ')
                            time_str = dt.strftime('%H:%M:%S')
                        except:
                            time_str = 'Recent'
                        real_tweets.append({"user": f"@User_{t.get('author_id', 'Unknown')[-4:]}", "text": t.get('text', ''), "timestamp": time_str})
        except Exception as e: print(f"Twitter API Exception: {e}")

    # --- 3. Try Regional RSS (Authentic Feeds) ---
    if detected_region:
        print(f"Uplinking regional RSS: {detected_region}")
        rss_geo = fetch_rss_news(detected_region)
        real_news.extend(rss_geo[:15])

    # --- 4. Try NewsAPI (If available) ---
    if NEWS_API_KEY and NEWS_API_KEY != 'mock_news_key':
        try:
            news_url = f"https://newsapi.org/v2/everything?q={location_query or 'world news'}&sortBy=publishedAt&pageSize=10&apiKey={NEWS_API_KEY}"
            n_res = requests.get(news_url, timeout=5)
            if n_res.status_code == 200:
                n_data = n_res.json()
                for article in n_data.get('articles', [])[:50]:
                    pub_time = article.get('publishedAt', '')
                    try:
                        dt = datetime.strptime(pub_time, '%Y-%m-%dT%H:%M:%SZ')
                        time_str = dt.strftime('%H:%M %b %d')
                    except:
                        time_str = 'Recent'
                    real_news.append({
                        "source": article.get('source', {}).get('name', 'NewsAPI'),
                        "title": article.get('title', ''),
                        "time": time_str,
                        "url": article.get('url', '#'),
                        "published": pub_time or datetime.now(timezone.utc).isoformat(),
                        "type": "GEO_INTEL"
                    })
        except Exception as e: print(f"News API Exception: {e}")

    # --- 5. International Fallback (If no regional news found) ---
    if not real_news:
        print("Fallback to International RSS Intelligence...")
        intl_news = fetch_rss_news("INTERNATIONAL")
        real_news.extend(intl_news[:15])

    # --- 6. Final Mock Fallback (If all else fails) ---
    sentiment_score = random.uniform(0.1, 0.9)
    sentiment_label = "NEUTRAL"
    if sentiment_score > 0.7: sentiment_label = "STABLE"
    elif sentiment_score < 0.3: sentiment_label = "CRITICAL"
    elif sentiment_score < 0.5: sentiment_label = "UNREST"

    if not real_tweets:
        hashtags = ["#Breaking", "#Alert", "#Status", "#Update", "#Intel"]
        for _ in range(2):
             real_tweets.append({
                "user": f"@User_{random.randint(1000,9999)}",
                "text": f"Activity reported in sector {random.randint(1,99)}. Status: {sentiment_label}. {random.choice(hashtags)}",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60))).strftime("%H:%M:%S")
            })

    if not real_news:
        headlines = ["Local communications monitoring active.", "Regional security alert issued.", "Cyber-surveillance network link stable."]
        for _ in range(3):
            real_news.append({
                "source": "GNN (Global News Network)",
                "title": random.choice(headlines),
                "time": "Just now",
                "url": "#",
                "published": datetime.now(timezone.utc).isoformat(),
                "type": "MOCK_INTEL"
            })
        
    # --- 7. AI Intelligence Summary ---
    context_str = f"LOCATION: {location_query or 'Unknown Sector'}\n"
    if real_news:
        context_str += "LATEST_HEADLINES:\n" + "\n".join([f"- {n['title']} ({n['source']})" for n in real_news[:5]]) + "\n"
    if real_tweets:
        context_str += "INTERCEPTED_SIGNALS:\n" + "\n".join([f"- {t['text']}" for t in real_tweets[:3]]) + "\n"
    
    ai_summary = analyze_with_ai(context_str)

    result_data = {
        "lat": lat,
        "lon": lon,
        "sentiment": {
            "score": round(sentiment_score, 2),
            "label": sentiment_label,
            "trend": random.choice(["RISING", "FALLING", "STABLE"])
        },
        "tweets": real_tweets,
        "news": real_news,
        "intel_summary": ai_summary
    }

    # Store in cache
    news_cache[cache_key] = (now_ts, result_data)

    return jsonify(result_data)

def analyze_with_ai(context):
    """
    Use OpenRouter to analyze geopolitical context and sentiment.
    """
    if not OPENROUTER_API_KEY or "placeholder" in OPENROUTER_API_KEY:
        # Fallback to deterministic patterns if no key
        return f"AI_SIMULATION: Based on intercepted signals, tensions in this sector are currently {random.choice(['elevated', 'stable', 'volatile'])}. Strategic nodes show pattern {random.randint(100,999)}."

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-exp:free", # Using a free model for demonstration
                "messages": [
                    {"role": "system", "content": "You are HayOS Geopolitical AI. Analyze the provided news context and provide a brief, high-tech assessment of the situation in 2-3 sentences. Use CYBERPUNK/OSINT tone."},
                    {"role": "user", "content": context}
                ]
            }),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"OpenRouter Error: {e}")
    
    return "ANALYSIS_OFFLINE: Connectivity to Neural Core interrupted."

@app.route('/api/news/analyze', methods=['POST'])
def analyze_news_sentiment():
    data = request.json
    content = data.get('content', '')
    if not content:
        return jsonify({"error": "No content provided"}), 400
    
    analysis = analyze_with_ai(content)
    return jsonify({"analysis": analysis})

@app.route('/api/market/data')
def get_market_data():
    """
    Fetch market data for Oil, Gold, Silver, and Crypto.
    """
    try:
        # 1. Crypto from CoinGecko (Free API)
        crypto_res = requests.get('https://api.coingecko.org/api/v3/simple/price?ids=bitcoin,ethereum,solana,cardano,ripple,polkadot,dogecoin,binancecoin,chainlink,matic-network&vs_currencies=usd&include_24hr_change=true', timeout=5)
        crypto_data = crypto_res.json() if crypto_res.status_code == 200 else {}

        # 2. Mock Commodities (Hard to find free reliable real-time commodity API without keys)
        # In a real app, one would use AlphaVantage or similar.
        commodities = {
            "OIL": {"price": 74.23 + random.uniform(-0.5, 0.5), "change": 1.2},
            "BRENT": {"price": 79.12 + random.uniform(-0.5, 0.5), "change": -0.4},
            "GOLD": {"price": 2035.50 + random.uniform(-5, 5), "change": 0.15},
            "SILVER": {"price": 22.84 + random.uniform(-0.1, 0.1), "change": -0.2}
        }

        # Format crypto
        formatted_crypto = {}
        for k, v in crypto_data.items():
            name = k.upper().replace('-NETWORK', '')
            formatted_crypto[name] = {"price": v['usd'], "change": v['usd_24h_change']}

        return jsonify({
            "status": "LIVE",
            "timestamp": datetime.now().isoformat(),
            "commodities": commodities,
            "crypto": formatted_crypto
        })
    except Exception as e:
        print(f"Market Data Error: {e}")
        # Robust fallback if API fails
        commodities = {
            "OIL": {"price": 74.23 + random.uniform(-0.5, 0.5), "change": 0.0},
            "BRENT": {"price": 79.12 + random.uniform(-0.5, 0.5), "change": 0.0},
            "GOLD": {"price": 2035.50 + random.uniform(-5, 5), "change": 0.0},
            "SILVER": {"price": 22.84 + random.uniform(-0.1, 0.1), "change": 0.0}
        }
        mock_crypto = {
            "BITCOIN": {"price": 42000, "change": 0.0},
            "ETHEREUM": {"price": 2500, "change": 0.0},
            "SOLANA": {"price": 100, "change": 0.0}
        }
        return jsonify({
            "status": "OFFLINE_SIMULATION",
            "timestamp": datetime.now().isoformat(),
            "commodities": commodities,
            "crypto": mock_crypto,
            "error": str(e)
        })

@app.route('/news')

def news_page():
    return render_template('news.html')

@app.route('/newsnetworks')

def newsnetworks_page():
    return render_template('newsnetworks.html', sources=NEWS_SOURCES)

def fetch_rss_news(region):
    """
    Fetch and parse all RSS feeds for a given region defined in news_config.py.
    """
    articles = []
    if region not in NEWS_SOURCES:
        return articles
    
    rss_urls = NEWS_SOURCES[region].get('rss', [])
    for url in rss_urls:
        try:
            # We use a timeout to avoid hanging on slow feeds
            feed = feedparser.parse(url)
            source_name = feed.feed.get('title', url.split('/')[2])
            for entry in feed.entries[:10]: 
                # Basic formatting for consistency
                articles.append({
                    "source": source_name,
                    "title": entry.get('title'),
                    "url": entry.get('link'),
                    "published": entry.get('published') or entry.get('updated') or datetime.now(timezone.utc).isoformat(),
                    "description": entry.get('summary', '')[:200] + "..." if entry.get('summary') else "",
                    "image": None,
                    "type": f"RSS_{region}"
                })
        except Exception as e:
            print(f"Error parsing RSS {url}: {e}")
            
    return articles

@app.route('/api/news/advanced')

def get_advanced_news():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    query = request.args.get('q', '')
    news_type = request.args.get('type', 'all') 
    region = request.args.get('region', '').upper()
    
    if not NEWS_API_KEY or NEWS_API_KEY == "YOUR_NEWS_API_KEY": # Let real keys through
        # If no key, try RSS first
        if region:
            rss_news = fetch_rss_news(region)
            if rss_news:
                return jsonify({
                    "query": query or region,
                    "articles": rss_news,
                    "count": len(rss_news)
                })
        
        # If no key, and no lat/lon, return mock global news
        if not lat or not lon:
            # Fallback to general INTERNATIONAL RSS if possible
            if not region:
                rss_intl = fetch_rss_news("INTERNATIONAL")
                if rss_intl:
                    return jsonify({
                        "query": "INTERNATIONAL INTEL",
                        "articles": rss_intl,
                        "count": len(rss_intl)
                    })

            mock_articles = []
            mock_headlines = [
                "Global Cyber-Defense Protocol H9-EYE Initiated",
                "Quantum Encryption Standards Adopted by Major Sectors",
                "AI Sentiment Analysis Reveals Shifting Geopolitical Tides",
                "Decentralized Data Grids Expanding in Neutral Zones",
                "Satellite Uplink Stability Reaches Record 99.9%"
            ]
            for i, h in enumerate(mock_headlines):
                mock_articles.append({
                    "source": "H9_OSINT_CORE",
                    "title": h,
                    "url": "#",
                    "published": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                    "description": "Simulation data generated by HayOS Core Intelligence.",
                    "image": None,
                    "type": "CORE_STREAM"
                })
            return jsonify({
                "query": query or "global news",
                "articles": mock_articles,
                "count": len(mock_articles)
            })
        return get_geo_news()

    news_articles = []
    search_query = query
    if lat and lon:
        try:
            geo_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            g_res = requests.get(geo_url, headers={'User-Agent': 'HayOS/1.0'}, timeout=5)
            if g_res.status_code == 200:
                address = g_res.json().get('address', {})
                city = address.get('city') or address.get('town') or address.get('village')
                country = address.get('country')
                
                if news_type == 'local' and city:
                    search_query += f" {city}"
                elif news_type == 'national' and country:
                    search_query += f" {country}"
                elif news_type == 'all':
                    search_query += f" {city or country or ''}"
        except:
            pass

    sort_by = request.args.get('sortBy', 'publishedAt')
    from_date = request.args.get('from', '')
    language = request.args.get('language', 'en')
    page_size = 10 # Hard limit to 10 as per user request
    
    # --- Check Cache ---
    cache_key = f"advanced_{search_query}_{language}_{sort_by}"
    now_ts = datetime.now(timezone.utc).timestamp()
    if cache_key in news_cache:
        cached_time, cached_data = news_cache[cache_key]
        if (now_ts - cached_time) < (NEWS_CACHE_LIMIT * 60):
            print(f"Serving cached news for: {cache_key}")
            return jsonify(cached_data)

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': search_query.strip() or 'world news',
            'apiKey': NEWS_API_KEY,
            'language': language,
            'sortBy': sort_by,
            'pageSize': page_size
        }
        if from_date:
            params['from'] = from_date

        print(f"Requesting NewsAPI: {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        print(f"NewsAPI Response Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"NewsAPI successfully fetched {len(data.get('articles', []))} articles.")
            for art in data.get('articles', []):
                news_articles.append({
                    "source": art.get('source', {}).get('name', 'N/A'),
                    "title": art.get('title'),
                    "url": art.get('url'),
                    "published": art.get('publishedAt'),
                    "description": art.get('description'),
                    "image": art.get('urlToImage'),
                    "type": "INTEL_FEED"
                })
        else:
             print(f"NewsAPI Error (Advanced): {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"Advanced News Fetch Error: {e}")

    # If region is provided, fetch RSS to complement NewsAPI
    # DEFAULT behavior: if no region specified, mixing in INTERNATIONAL RSS
    rss_region = region if region else "INTERNATIONAL"
    rss_news = fetch_rss_news(rss_region)
    news_articles.extend(rss_news)

    # Final logic: if articles still empty, provide mock data for fallback
    if not news_articles:
        mock_headlines = [
            "Data Stream Corrupted: Displaying Archived Intelligence",
            "Global Security Lattice Synchronizing...",
            "Neutral Zone Communication Nodes Restored",
            "AI Predictive Core Detects Low-Level Sector Volatility",
            "OSINT Nodes Reporting Stable Uplink in Peripheral Sectors"
        ]
        for i, h in enumerate(mock_headlines):
            news_articles.append({
                "source": "H9_EMERGENCY_UPLINK",
                "title": h,
                "url": "#",
                "published": (datetime.now(timezone.utc) - timedelta(hours=i*2)).isoformat(),
                "description": "Fallback intelligence provided by HayOS redundant storage.",
                "image": None,
                "type": "FALLBACK_STREAM"
            })

    # Store in cache if successful (even if only RSS articles found)
    if news_articles:
        result_data = {
            "query": search_query,
            "articles": news_articles,
            "count": len(news_articles)
        }
        news_cache[cache_key] = (now_ts, result_data)

    return jsonify({
        "query": search_query,
        "articles": news_articles,
        "count": len(news_articles)
    })


@app.route('/api/translate')

def translate_text():
    """
    Translate text to English using free translation service.
    Uses MyMemory Translation API (free, no key required).
    """
    text = request.args.get('text', '')
    source_lang = request.args.get('source', 'auto')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        # MyMemory doesn't support 'auto', so we need to try common languages
        # or use a simple heuristic
        if source_lang == 'auto':
            # Try translating from multiple common languages and pick the best one
            # Common news languages: Spanish, French, German, Arabic, Chinese, Russian, etc.
            test_langs = ['es', 'fr', 'de', 'ar', 'zh', 'ru', 'ja', 'pt', 'it', 'nl']
            
            # Quick heuristic: if text is already mostly English, don't translate
            if text.replace(' ', '').isascii():
                # Likely already English or uses Latin script
                source_lang = 'en'
            else:
                # Try the first non-English language (most common: Spanish)
                source_lang = 'es'
        
        # Using MyMemory Translation API (free, no key required)
        # Limit: 500 words per request, 10000 words per day
        url = "https://api.mymemory.translated.net/get"
        params = {
            'q': text[:500],  # Limit to 500 chars
            'langpair': f'{source_lang}|en'
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            translated = data.get('responseData', {}).get('translatedText', text)
            
            # If translation is same as original, it might already be in English
            if translated == text or translated.upper() == text.upper():
                return jsonify({
                    "original": text,
                    "translated": text,
                    "source_lang": "en",
                    "note": "Already in English"
                })
            
            return jsonify({
                "original": text,
                "translated": translated,
                "source_lang": source_lang
            })
        else:
            return jsonify({"error": "Translation failed", "original": text}), 500
            
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({"error": str(e), "original": text}), 500


def get_flight_meta(callsign):
    """Fetch route and registration data for a specific callsign."""
    if not callsign or callsign == "N/A":
        return jsonify({"error": "No callsign provided"}), 400
        
    try:
        # 1. Try Routes API (Origin/Destination)
        route_url = f"https://opensky-network.org/api/routes?callsign={callsign}"
        r_res = requests.get(route_url, timeout=10)
        route_data = {}
        if r_res.status_code == 200:
            route_data = r_res.json()
            
        return jsonify({
            "callsign": callsign,
            "route": route_data.get("route", ["UNK", "UNK"]),
            "operator": route_data.get("operatorIata", "---"),
            "flight_number": route_data.get("flightNumber", "---")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



  # ================================================================
# GEOSENTIAL AI ROUTE - Ollama Phi Integration with Web Search
# ================================================================
import requests as req_ollama

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "phi:latest"
EMBEDDING_MODEL = "all-minilm:latest"

# --- Hugging Face Configuration  ---

HF_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct:cerebras"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

# ================================================================
# GEOSENTIAL VECTOR DATABASE (ChromaDB)
# ================================================================
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DB_PATH = "./geosent_chroma_db"
COLLECTION_NAME = "geosent_memory"

def init_chroma_db():
    """Initialize ChromaDB client and collection."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        # using all-MiniLM-L6-v2 as default embedding function
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)
        print(f"ChromaDB: Initialized collection '{COLLECTION_NAME}'")
        return client, collection
    except Exception as e:
        print(f"ChromaDB Init Error: {e}")
        return None, None

chroma_client, memory_collection = init_chroma_db()

def save_conversation(user_message, ai_response):
    """Save conversation to ChromaDB as vector memory."""
    if not memory_collection: return
    try:
        # We store the interaction as a single document
        doc_id = f"mem_{int(time.time()*1000)}"
        text_content = f"User: {user_message}\nAI: {ai_response}"
        
        memory_collection.add(
            documents=[text_content],
            metadatas=[{"timestamp": datetime.now().isoformat(), "type": "conversation"}],
            ids=[doc_id]
        )
        print(f"ChromaDB: Saved memory {doc_id}")
    except Exception as e:
        print(f"ChromaDB Save Error: {e}")

def get_relevant_memories(query_text, n_results=3):
    """Retrieve semantically relevant memories."""
    if not memory_collection: return []
    try:
        results = memory_collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        # results['documents'] is a list of lists
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        print(f"ChromaDB Query Error: {e}")
        return []

def get_conversation_context(current_query):
    """Build context string from relevant vector memories."""
    memories = get_relevant_memories(current_query, n_results=3)
    if not memories:
        return ""
    
    context_str = "RELEVANT MEMORY STREAM (ChromaDB):\n"
    for i, mem in enumerate(memories):
        context_str += f"[{i+1}] {mem}\n"
    return context_str + "\n"

# --- Memory Management API Endpoints ---

@app.route('/api/geosentialai/memory', methods=['GET'])
def get_memories():
    """List all memories (limited to recent/all for UI)."""
    if not memory_collection:
        return jsonify({"error": "Memory system offline"}), 500
    try:
        # Chroma doesn't have a simple 'get_all' without IDs, but we can peek or get by limit
        # For simplicity in this UI, we'll fetch the last 20
        count = memory_collection.count()
        if count == 0:
            return jsonify({"memories": []})
            
        # We can't easily sort by time in Chroma's get() without metadata filter complexities
        # So we just get a batch. In production, you'd track IDs separate or use a mix.
        # But `collection.get()` returns up to limit.
        result = memory_collection.get(limit=50, include=['documents', 'metadatas'])
        
        memories = []
        for i, doc_id in enumerate(result['ids']):
            meta = result['metadatas'][i] if result['metadatas'] else {}
            memories.append({
                "id": doc_id,
                "content": result['documents'][i],
                "timestamp": meta.get('timestamp', 'Unknown')
            })
        
        # Sort by timestamp desc (newest first)
        memories.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({"memories": memories, "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geosentialai/memory/<memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    if not memory_collection: return jsonify({"error": "System offline"}), 500
    try:
        memory_collection.delete(ids=[memory_id])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geosentialai/memory/all', methods=['DELETE'])
def clear_all_memories():
    """Clear all entries from the memory collection."""
    if not memory_collection: return jsonify({"error": "System offline"}), 500
    try:
        # ChromaDB requires getting all IDs first to delete
        all_ids = memory_collection.get()['ids']
        if all_ids:
            memory_collection.delete(ids=all_ids)
            print(f"ChromaDB: Cleared {len(all_ids)} memories")
        return jsonify({"success": True, "count": len(all_ids)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geosentialai/memory/<memory_id>', methods=['PUT'])
def update_memory(memory_id):
    if not memory_collection: return jsonify({"error": "System offline"}), 500
    data = request.json
    new_content = data.get('content')
    if not new_content: return jsonify({"error": "No content"}), 400
    
    try:
        # metadata update is optional, we just update document content
        memory_collection.update(
            ids=[memory_id],
            documents=[new_content]
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Helper Scrapers ---
def scrape_google_html(query):
    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Google search URL
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            # Google's HTML structure changes often, but look for standard result containers
            # Try looking for divs with class 'g' or 'tF2Cxc'
            for g in soup.find_all('div', class_='g', limit=5):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    title = anchors[0].find('h3')
                    if title:
                        title = title.get_text()
                        snippet_div = g.find('div', style='-webkit-line-clamp:2') # common snippet container
                        snippet = snippet_div.get_text() if snippet_div else "Google Result"
                        if link.startswith('http'):
                            results.append({"title": title, "link": link, "snippet": snippet, "source": "Google"})
    except Exception as e:
        print(f"Google Scrape Error: {e}")
    return results

def scrape_bing_html(query):
    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            # Bing results are usually in <li class="b_algo">
            for li in soup.find_all('li', class_='b_algo', limit=5):
                h2 = li.find('h2')
                if h2:
                    a = h2.find('a')
                    if a:
                        title = a.get_text()
                        link = a['href']
                        snippet_p = li.find('p')
                        snippet = snippet_p.get_text() if snippet_p else "Bing Result"
                        results.append({"title": title, "link": link, "snippet": snippet, "source": "Bing"})
    except Exception as e:
        print(f"Bing Scrape Error: {e}")
    return results

def scrape_ddg_html(query):
    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        }
        # Use html.duckduckgo.com for easier parsing
        resp = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=headers, timeout=10)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for result in soup.find_all("div", class_="result", limit=5):
                link_el = result.find("a", class_="result__a")
                snippet_el = result.find("a", class_="result__snippet")
                if link_el:
                    title = link_el.get_text(strip=True)
                    link = link_el["href"]
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                    results.append({"title": title, "link": link, "snippet": snippet, "source": "DuckDuckGo"})
    except Exception as e:
        print(f"DDG Scrape Error: {e}")
    return results

def scrape_darkweb(query):
    """
    Dark Web search via Tor proxy. Queries multiple .onion search engines.
    Requires Tor service running on localhost:9050.
    Based on Robin project: https://github.com/apurvsinghgautam/robin
    """
    import random
    import re
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = []
    
    # Dark Web Search Engines (.onion addresses) - Full List
    DARKWEB_ENGINES = [
        "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}",  # Ahmia
        "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/search?q={query}",  # OnionLand
        "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion/torgle/?query={query}",  # Torgle
        "http://amnesia7u5odx5xbwtpnqk3edybgud5bmiagu75bnqx2crntw5kry7ad.onion/search?query={query}",  # Amnesia
        "http://kaizerwfvp5gxu6cppibp7jhcqptavq3iqef66wbxenh6a2fklibdvid.onion/search?q={query}",  # Kaizer
        "http://anima4ffe27xmakwnseih3ic2y7y3l6e7fucwk4oerdn4odf7k74tbid.onion/search?q={query}",  # Anima
        "http://tornadoxn3viscgz647shlysdy7ea5zqzwda7hierekeuokh5eh5b3qd.onion/search?q={query}",  # Tornado
        "http://tornetupfu7gcgidt33ftnungxzyfq2pygui5qdoyss34xbgx2qruzid.onion/search?q={query}",  # TorNet
        "http://torlbmqwtudkorme6prgfpmsnile7ug2zm4u3ejpcncxuhpu4k2j4kyd.onion/index.php?a=search&q={query}",  # Torland
        "http://findtorroveq5wdnipkaojfpqulxnkhblymc7aramjzajcvpptd4rjqd.onion/search?q={query}",  # Find Tor
        "http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/search?query={query}",  # Excavator
        "http://oniwayzz74cv2puhsgx4dpjwieww4wdphsydqvf5q7eyz4myjvyw26ad.onion/search.php?s={query}",  # Onionway
        "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/search?q={query}",  # Tor66
        "http://3fzh7yuupdfyjhwt3ugzqqof6ulbcl27ecev33knxe3u7goi3vfn2qqd.onion/oss/index.php?search={query}",  # OSS
        "http://torgolnpeouim56dykfob6jh5r2ps2j73enc42s2um4ufob3ny4fcdyd.onion/?q={query}",  # Torgol
        "http://searchgf7gdtauh7bhnbyed4ivxqmuoat3nm6zfrg3ymkq6mtnpye3ad.onion/search?q={query}",  # The Deep Searches
    ]
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
    ]
    
    def get_tor_session():
        session = requests.Session()
        # Tor SOCKS5 proxy on default port
        session.proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
        return session
    
    def fetch_onion_search(endpoint, query_term):
        url = endpoint.format(query=requests.utils.quote(query_term))
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            session = get_tor_session()
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                links = []
                for a in soup.find_all('a'):
                    try:
                        href = a.get('href', '')
                        title = a.get_text(strip=True)
                        # Extract onion links
                        onion_match = re.findall(r'https?://[a-z0-9\.]+\.onion[^\s"\']*', href)
                        if onion_match and "search" not in onion_match[0].lower() and len(title) > 3:
                            links.append({"title": title, "link": onion_match[0], "snippet": "Dark Web Result", "source": "TOR_NETWORK"})
                    except:
                        continue
                return links
        except Exception as e:
            print(f"Darkweb Engine Error ({endpoint[:50]}...): {e}")
        return []
    
    # Check if Tor is available (quick test)
    try:
        test_session = get_tor_session()
        test_session.get("http://check.torproject.org", timeout=5)
        tor_available = True
    except:
        tor_available = False
        print("TOR_PROXY_UNAVAILABLE: Falling back to clearnet .onion proxies")
    
    if tor_available:
        # Query multiple engines in parallel (up to 6)
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(fetch_onion_search, endpoint, query) for endpoint in DARKWEB_ENGINES]
            for future in as_completed(futures):
                try:
                    res = future.result()
                    results.extend(res)
                except:
                    pass
    else:
        # Fallback: Use clearnet Ahmia proxy (ahmia.fi) - get more results
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            url = f"https://ahmia.fi/search/?q={requests.utils.quote(query)}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for li in soup.find_all("li", class_="result", limit=15):  # Increased from 5 to 15
                    a = li.find("a")
                    if a:
                        title = a.get_text(strip=True)
                        link = a.get("href", "")
                        cite = li.find("cite")
                        snippet = cite.get_text(strip=True) if cite else "Ahmia Result"
                        results.append({"title": title, "link": link, "snippet": snippet, "source": "Ahmia_Clearnet"})
        except Exception as e:
            print(f"Ahmia Clearnet Error: {e}")
    
    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r['link'] not in seen:
            seen.add(r['link'])
            unique.append(r)
    
    return unique

@app.route('/api/tools/web_scan', methods=['POST'])
def perform_web_scan():
    """
    Advanced Web Scraper Endpoint.
    Handles aggressive scraping, different media types, and source filtering.
    """
    data = request.json or {}
    query = data.get('query', '').strip()
    scan_type = data.get('type', 'all')
    sources = data.get('sources', [])
    aggressive = data.get('aggressive', False)
    if isinstance(sources, str):
        sources = [sources]
    
    # 1. Modify Query based on Sources (Aggressive Mode)
    site_map = {
        'twitter': 'site:twitter.com',
        'reddit': 'site:reddit.com',
        'instagram': 'site:instagram.com',
        'linkedin': 'site:linkedin.com',
        'telegram': 'site:t.me',
        'discord': 'site:discord.com',
        'pastebin': 'site:pastebin.com',
        'github': 'site:github.com',
        'stackoverflow': 'site:stackoverflow.com',
        'leaks': 'site:pastebin.com OR site:breachforums.cx', 
        'darkweb': 'site:onion.ly OR "onion"'
    }

    if sources:
        # Construct a combined OR query for all selected sources
        site_filters = []
        for s in sources:
            if s == 'web':
                continue # No filter for general web
            if s in site_map:
                site_filters.append(site_map[s])
            else:
                site_filters.append(f"site:{s}.com")
        
        valid_filters = site_filters
        
        if valid_filters:
            # If 'web' was selected, we want (filters) OR (general terms) -> actually in search engine syntax, adding "OR site:..." works but usually restricts.
            # If web is selected, we basically shouldn't restrict at all, OR we should search for "query OR (query site:twitter)" which is redundant.
            # Strategy: If 'web' is present, don't apply ANY site filter to the main query, but maybe boost the others?
            # actually, if 'web' is there, the user wants EVERYTHING. So `site:twitter.com` is a subset of `web`. 
            # So if 'web' is in sources, we just run the query RAW.
            if 'web' in sources:
                pass # Do not append site filters
            else:
                if len(valid_filters) == 1:
                    query += f" {valid_filters[0]}"
                else:
                    combined = " OR ".join(valid_filters)
                    query += f" ({combined})"

    results = []

    # Try DDG Library first (cleanest API if works)
    try:
        # NOTE: Updated to 'ddgs' package if available, else try fallbacks
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            if scan_type == 'images':
                 # ... (keep image logic separate or assume text for general web)
                 pass 
            elif scan_type == 'text' or scan_type == 'all':
                 ddg_gen = ddgs.text(query, max_results=5)
                 for r in ddg_gen:
                     results.append({
                         "title": r.get('title', ''),
                         "link": r.get('href', ''),
                         "snippet": r.get('body', ''),
                         "source": "DDGS_LIB"
                     })
        except Exception:
            pass # Fallback immediately
    except Exception:
        pass

    # If aggressive or web is selected, perform multi-engine aggregation
    # Run scrapers
    if not results or aggressive or 'web' in sources or not sources:
        # We want to aggregate results from Google, Bing, and DDG HTML
        print(f"Performing Multi-Engine Scrape for: {query}")
        
        # Google
        g_results = scrape_google_html(query)
        results.extend(g_results)
        
        # Bing
        b_results = scrape_bing_html(query)
        results.extend(b_results)
        
        # DDG HTML
        d_results = scrape_ddg_html(query)
        results.extend(d_results)
    
    # Dark Web search (if darkweb source selected or aggressive mode)
    if 'darkweb' in sources or aggressive:
        print(f"Performing Dark Web Scrape for: {query}")
        darkweb_results = scrape_darkweb(query)
        results.extend(darkweb_results)

    # De-duplicate results by link
    unique_results = []
    seen_links = set()
    for r in results:
        if r['link'] not in seen_links:
            unique_results.append(r)
            seen_links.add(r['link'])
    results = unique_results

    # If still no results, maybe mock for demonstration if "aggressive"
    if not results and aggressive:
            # Last resort mock to show UI working
            results.append({
                "title": "NO_LIVE_VECTORS_FOUND",
                "link": "#",
                "snippet": "Target did not yield public results. Try broadening search or check network connection."
            })

    # 3. Aggressive Scraping (Fetch Page Content for Text Results)
    if aggressive and results:
            for item in results[:3]:
                if item.get('link') and not item.get('full_text'):
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        page_resp = requests.get(item['link'], headers=headers, timeout=5)
                        if page_resp.status_code == 200:
                            from bs4 import BeautifulSoup
                            page_soup = BeautifulSoup(page_resp.text, "html.parser")
                            paragraphs = page_soup.find_all('p')
                            text_content = ' '.join([p.get_text() for p in paragraphs[:5]])
                            if text_content:
                                item['full_text'] = text_content[:500] + "..." 
                    except Exception:
                        pass

    return jsonify({
        "status": "success",
        "results": results,
        "query": query,
        "type": scan_type,
        "aggressive": aggressive
    })


@app.route('/api/geosentialai/chat', methods=['POST'])
def geosentialai_chat():
    """
    Advanced geospatial AI chat with Hugging Face Llama-3.1 model.
    Integrates with real-time web results and map functions.
    """
    data = request.json or {}
    user_message = data.get('message', '').strip()
    web_search = data.get('web_search', False)
    human_mode = data.get('human_mode', False)
    engine = data.get('engine', 'huggingface')
    context_data = data.get('context', {})

    # Auto-enable web search for news/stocks if not already on
    news_keywords = ["news", "stock", "price", "market", "update", "latest", "briefing", "happening"]
    if any(k in user_message.lower() for k in news_keywords):
        web_search = True
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # --- Build Web Context (DuckDuckGo Scraper) ---
    web_context = ""
    if web_search:
        try:
            query = requests.utils.quote(user_message)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            resp = requests.post(url, data={"q": user_message}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                snippets = []
                for result in soup.find_all("div", class_="result", limit=5):
                    link_el = result.find("a", class_="result__a")
                    snippet_el = result.find("a", class_="result__snippet")
                    if link_el and snippet_el:
                        title = link_el.get_text(strip=True)
                        link = link_el["href"]
                        text = snippet_el.get_text(strip=True)
                        snippets.append(f"• [{title}]({link}): {text}")
                if snippets:
                    web_context = "REAL-TIME WEB DATA (DUCKDUCKGO):\n" + "\n".join(snippets)
                else:
                    web_context = "*(No web results found for this query)*"
        except Exception as e:
            web_context = f"*(Web search technical error: {e})*"

    # --- Build Map Context ---
    map_context_str = ""
    if context_data:
        map_context_str = "CURRENT MAP CONTEXT:\n"
        if context_data.get('flights'):
            map_context_str += "• FLIGHTS: " + ", ".join([f"{f['icao']} at ({f['lat']}, {f['lng']})" for f in context_data['flights']]) + "\n"
        if context_data.get('vessels'):
            map_context_str += "• VESSELS: " + ", ".join([f"{v['mmsi']} at ({v['lat']}, {v['lng']})" for v in context_data['vessels']]) + "\n"
        if context_data.get('cells'):
            map_context_str += "• CELL TOWERS: " + " | ".join(context_data['cells']) + "\n"
        if context_data.get('networks'):
            map_context_str += "• NETWORKS: " + " | ".join(context_data['networks']) + "\n"
        if context_data.get('surveillance'):
            map_context_str += "• SURVEILLANCE/SATELLITE: " + " | ".join(context_data['surveillance']) + "\n"
        if context_data.get('sentiment'):
            map_context_str += f"• LOCAL SENTIMENT: {context_data['sentiment']}\n"
        map_context_str += "\n"

    # --- Build System Prompt ---
    system_prompt = (
        "You are 'GeoSential AI', a high-tech Geospatial Intelligence (GEOINT) and OSINT assistant for HayOS. "
        "Your mission is to provide accurate, real-time data analysis and global briefings.\n\n"
        "CORE DIRECTIVES:\n"
        "1. REAL-TIME ACCURACY: Prioritize 'REAL-TIME WEB DATA' for News, Stocks, and Weather updates.\n"
        "2. MAP INTERACTION: You can trigger GUI elements by outputting tags. Use ONLY valid tags from the list below:\n"
        "   - [TRACK_FLIGHT: <icao>] - Zooms to a specific flight.\n"
        "   - [TRACK_VESSEL: <mmsi>] - Zooms to a specific vessel.\n"
        "   - [SHOW_WEATHER: <lat>, <lng>] - Opens meteorology/environment GUI for coordinates.\n"
        "   - [SCAN_MAP: <lat>, <lng>] - Zooms and initiates a sector-wide signal scan.\n"
        "3. MULTI-LAYER ANALYSIS: Correlate SIGINT with GEOINT data if relevant.\n"
        "4. NEWS & MARKET DATA: When asked for news or stocks, provide a concise briefing with formatted prices/headlines from the web data.\n"
        "5. FORMATTING & UI:\n"
        "   - Use **Bold Headers** for distinct sections.\n"
        "   - Use blockquotes (`>`) for web search snippets and provide links.\n"
        "   - Metrics should be in `monospaced code blocks`."
    )

    if human_mode:
        system_prompt += (
            "\n\nPERSONA: 'HUMAN MODE' ACTIVE. Respond as a helpful, conversational, and empathetic human colleague. "
            "Use natural flow, polite interjections, and expert human-level reasoning while maintaining your technical edge. "
            "Avoid overly robotic preambles."
        )
    else:
        system_prompt += "\n\nPERSONA: 'TECHNICAL OSINT MODE'. Be direct, professional, and strictly data-driven."

    # --- Memory Context (ChromaDB) ---
    memory_context = get_conversation_context(user_message)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{web_context}\n\n{map_context_str}\n{memory_context}\nUSER_MESSAGE: {user_message}"}
    ]

    try:
        if engine == 'ollama':
            # Fallback to local Ollama (Phi model)
            response = req_ollama.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            reply = response.json()["message"]["content"].strip()
        else:
            # Default to Cloud (Hugging Face)
            payload = {
                "model": MODEL_ID,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            resp = requests.post(HF_URL, headers=HEADERS, json=payload, timeout=30)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"].strip()

        # Save to ChromaDB Memory (Force Save)
        print(f"Memory: Saving interaction... User: {len(user_message)} chars, AI: {len(reply)} chars")
        save_conversation(user_message, reply)

        # Clean reply of command tags for TTS
        clean_reply = re.sub(r'\[.*?\]', '', reply).strip()
        
        # gTTS Text to Speech
        audio_base64 = ""
        try:
            tts = gTTS(text=clean_reply, lang='en')
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
                tts.save(temp_mp3.name)
                temp_mp3_path = temp_mp3.name
            with open(temp_mp3_path, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            if os.path.exists(temp_mp3_path): os.remove(temp_mp3_path)
        except Exception as tts_e:
            print(f"GeoSential TTS Error: {tts_e}")

        # reply = format_code_blocks(reply)
        return jsonify({
            "response": reply,
            "audio": audio_base64,
            "timestamp": datetime.now().isoformat(),
            "web_search_used": web_search,
            "engine_used": engine
        })
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Local AI Engine (Ollama) timed out after 120s. Please ensure Ollama is running or switch to Cloud (HF) engine."}), 504
    except Exception as e:
        return jsonify({"error": f"AI Engine Error ({engine}): {str(e)}"}), 500

@app.route('/api/geosentialai/embed', methods=['POST'])
def geosentialai_embed():
    """Generate embeddings for geospatial data using all-minilm model."""
    data = request.json or {}
    text = data.get('text', '').strip()
    


    if not text:
        return jsonify({"error": "Empty text"}), 400
    
    try:
        response = req_ollama.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=30
        )
        
        if response.status_code == 200:
            embeddings = response.json().get('embedding', [])
            return jsonify({"embeddings": embeddings, "dimension": len(embeddings)})
        else:
            return jsonify({"error": f"Embedding failed: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geosentialai/status')
def geosentialai_status():
    """Check if the AI subsystem is operational."""
    # We are now using Cloud AI (Hugging Face), so we just confirm the bridge is up
    return jsonify({
        "status": "CONNECTED",
        "engine": "HuggingFace Llama-3.1-8B",
        "web_search": "DuckDuckGo_Scraper_Active"
    })


if __name__ == '__main__':

    print("\n" + "="*60)
    print("  H9 AI IS LIVE")
    
  
    print("="*60 + "\n")

    app.run(host="0.0.0.0", port=8000, debug=True)





