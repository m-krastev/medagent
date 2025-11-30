import requests
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_location_from_ip(ip_address: str = '') -> str:
    """Gets location information based on an IP address using a geolocation API."""
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            json = response.json()
            return json.get("city", "Unknown") + ", " + json.get("country", "Unknown")
        else:
            logger.warning(f"Failed to get location for IP {ip_address}: {response.status_code}")
            return "Unknown"
    except Exception as e:
        logger.error(f"Error occurred while getting location for IP {ip_address}: {e}")
        return "Unknown"