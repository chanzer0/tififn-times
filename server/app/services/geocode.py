import requests
import time
from typing import Optional, Tuple
from app.core.config import settings


class GeocodingService:
    def __init__(self):
        self.service = settings.geocoding_service
        self.api_key = settings.geocoding_api_key
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.rate_limit_delay = 1.0  # Nominatim requires 1 second between requests
        
    def geocode_address(self, address: str) -> Optional[Tuple[float, float, str]]:
        """
        Geocode an address and return (latitude, longitude, formatted_address)
        Returns None if geocoding fails
        """
        if not address or not address.strip():
            return None
            
        try:
            # Check if this is an intersection
            if self._is_intersection(address):
                return self._geocode_intersection(address)
            else:
                # Clean the address for better geocoding
                cleaned_address = self._clean_address(address)
                
                if self.service == "nominatim":
                    return self._geocode_nominatim(cleaned_address)
                else:
                    raise ValueError(f"Unsupported geocoding service: {self.service}")
                
        except Exception as e:
            print(f"Geocoding error for address '{address}': {e}")
            return None
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address for better geocoding"""
        # Remove common prefixes/suffixes that might confuse geocoding
        cleaned = address.strip()
        
        # Add state if not present (Johnson County, Iowa area)
        if "ia" not in cleaned.lower() and "iowa" not in cleaned.lower():
            cleaned += ", IA"
            
        return cleaned
    
    def _geocode_nominatim(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Geocode using Nominatim (OpenStreetMap)"""
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "us"  # Limit to US addresses
        }
        
        headers = {
            "User-Agent": "TiffinTimes/1.0 (emergency-logs-mapping)"
        }
        
        try:
            # Respect rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            if results and len(results) > 0:
                result = results[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                formatted_address = result.get("display_name", address)
                
                return (lat, lon, formatted_address)
            else:
                # Try fallback strategies for rural addresses
                return self._try_fallback_geocoding(address)
                
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Nominatim geocoding error: {e}")
            
        return None
    
    def _try_fallback_geocoding(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Try fallback strategies for rural addresses that don't geocode directly"""
        # Extract street and city from address
        parts = address.split(',')
        if len(parts) < 2:
            return None
            
        street_part = parts[0].strip()
        city_part = parts[1].strip()
        
        # Strategy 1: Try just the street name without house number
        street_tokens = street_part.split()
        if len(street_tokens) > 1 and street_tokens[0].isdigit():
            # Remove house number and try street name + city
            street_without_number = ' '.join(street_tokens[1:])
            fallback_query = f"{street_without_number}, {city_part}"
            
            result = self._geocode_nominatim_direct(fallback_query)
            if result:
                lat, lon, formatted = result
                return (lat, lon, f"{address} (street-level approximation)")
        
        # Strategy 2: Try just the city
        result = self._geocode_nominatim_direct(city_part)
        if result:
            lat, lon, formatted = result
            return (lat, lon, f"{address} (city-level approximation)")
        
        # Strategy 3: Try broader area searches
        area_queries = [
            f"{city_part}, Johnson County, IA",
            f"{city_part}, Iowa",
            "Johnson County, IA"
        ]
        
        for query in area_queries:
            result = self._geocode_nominatim_direct(query)
            if result:
                lat, lon, formatted = result
                return (lat, lon, f"{address} (area approximation)")
        
        return None
    
    def _geocode_nominatim_direct(self, query: str) -> Optional[Tuple[float, float, str]]:
        """Direct Nominatim call without additional processing"""
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "us"
        }
        
        headers = {
            "User-Agent": "TiffinTimes/1.0 (emergency-logs-mapping)"
        }
        
        try:
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            if results and len(results) > 0:
                result = results[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                formatted_address = result.get("display_name", query)
                return (lat, lon, formatted_address)
                
        except Exception as e:
            print(f"Direct geocoding failed for '{query}': {e}")
            
        return None
    
    def _is_intersection(self, address: str) -> bool:
        """Detect if address is an intersection"""
        return '/' in address
    
    def _geocode_intersection(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Enhanced intersection geocoding with multiple strategies"""
        print(f"   Detected intersection: {address}")
        
        # Extract city/state from address
        city_state = self._extract_city_state(address)
        street1, street2 = self._parse_intersection(address)
        
        if not street1 or not street2:
            print(f"   Could not parse streets from: {address}")
            return None
        
        print(f"   Parsed as: '{street1}' & '{street2}' in {city_state}")
        
        # Strategy 1: Standard intersection formats
        intersection_formats = [
            f"{street1} & {street2}, {city_state}",
            f"{street1} and {street2}, {city_state}",
            f"intersection of {street1} and {street2}, {city_state}",
        ]
        
        for format_attempt in intersection_formats:
            print(f"   Trying format: {format_attempt}")
            result = self._geocode_nominatim(format_attempt)
            if result:
                print(f"   ✓ Success with format: {format_attempt}")
                return result
        
        # Strategy 2: Try simplified street names (remove directionals)
        simple_street1 = self._simplify_street_name(street1)
        simple_street2 = self._simplify_street_name(street2)
        
        if simple_street1 != street1 or simple_street2 != street2:
            simplified_formats = [
                f"{simple_street1} & {simple_street2}, {city_state}",
                f"{simple_street1} and {simple_street2}, {city_state}",
            ]
            
            for format_attempt in simplified_formats:
                print(f"   Trying simplified: {format_attempt}")
                result = self._geocode_nominatim(format_attempt)
                if result:
                    print(f"   ✓ Success with simplified: {format_attempt}")
                    return result
        
        # Strategy 3: Fallback to individual streets and calculate midpoint
        print(f"   Trying fallback: individual street geocoding")
        return self._geocode_intersection_fallback(street1, street2, city_state)
    
    def _extract_city_state(self, address: str) -> str:
        """Extract city and state from address"""
        # Look for city names we know about in Johnson County
        cities = ['iowa city', 'north liberty', 'coralville', 'tiffin', 'solon', 'swisher']
        address_lower = address.lower()
        
        for city in cities:
            if city in address_lower:
                return f"{city.title()}, IA"
        
        # Default fallback
        return "Iowa City, IA"
    
    def _parse_intersection(self, address: str) -> Tuple[str, str]:
        """Parse intersection into two street names"""
        # Remove city/state portion
        address_part = address.split(',')[0].strip()
        
        # Split on common intersection separators
        separators = ['/', ' & ', ' AND ', ' and ', ' AT ', ' at ', ' @ ']
        
        for sep in separators:
            if sep in address_part:
                parts = address_part.split(sep, 1)
                if len(parts) == 2:
                    street1 = parts[0].strip()
                    street2 = parts[1].strip()
                    return street1, street2
        
        return "", ""
    
    def _simplify_street_name(self, street: str) -> str:
        """Remove directionals and common prefixes"""
        # Remove directionals
        directionals = ['N ', 'S ', 'E ', 'W ', 'NE ', 'NW ', 'SE ', 'SW ']
        simplified = street
        
        for direction in directionals:
            if simplified.startswith(direction):
                simplified = simplified[len(direction):]
                break
        
        return simplified.strip()
    
    def _geocode_intersection_fallback(self, street1: str, street2: str, city_state: str) -> Optional[Tuple[float, float, str]]:
        """Fallback: geocode individual streets and calculate midpoint"""
        try:
            # Extract just the city name from city_state (e.g., "Swisher, IA" -> "Swisher")
            city_only = city_state.split(',')[0].strip()
            
            # Try different formats for geocoding streets
            street1_queries = [
                f"{street1}, {city_state}",
                f"{street1}, {city_only}",
                f"{street1} near {city_only}, IA"
            ]
            
            street2_queries = [
                f"{street2}, {city_state}",
                f"{street2}, {city_only}",
                f"{street2} near {city_only}, IA"
            ]
            
            # Try to geocode first street
            result1 = None
            for query in street1_queries:
                print(f"   Trying street 1: {query}")
                result1 = self._geocode_nominatim(query)
                if result1:
                    break
            
            # Try to geocode second street
            result2 = None
            for query in street2_queries:
                print(f"   Trying street 2: {query}")
                result2 = self._geocode_nominatim(query)
                if result2:
                    break
            
            if result1 and result2:
                lat1, lon1, _ = result1
                lat2, lon2, _ = result2
                
                # Calculate midpoint
                mid_lat = (lat1 + lat2) / 2
                mid_lon = (lon1 + lon2) / 2
                
                formatted_address = f"Intersection of {street1} and {street2}, {city_state} (approximated)"
                print(f"   ✓ Calculated intersection midpoint: ({mid_lat}, {mid_lon})")
                
                return (mid_lat, mid_lon, formatted_address)
            else:
                # If individual street geocoding fails, try more general queries
                if not result1:
                    print(f"   ✗ Could not geocode street 1: {street1}")
                if not result2:
                    print(f"   ✗ Could not geocode street 2: {street2}")
                    
                # Last resort: try geocoding just the city
                city_result = self._geocode_nominatim(city_state)
                if city_result:
                    lat, lon, _ = city_result
                    formatted_address = f"Near {street1} and {street2}, {city_state} (city center)"
                    print(f"   ⚠ Using city center as approximation: ({lat}, {lon})")
                    return (lat, lon, formatted_address)
                    
                return None
                
        except Exception as e:
            print(f"   ✗ Fallback geocoding failed: {e}")
            return None


# Global geocoding service instance
geocoding_service = GeocodingService()