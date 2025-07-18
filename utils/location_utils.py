#!/usr/bin/env python3
"""
Location validation utilities for the Face Recognition Attendance System.
This module handles location-based validation for attendance marking.
"""

import logging
from flask import request
from database.models import OfficeLocation
from config.config import Config

logger = logging.getLogger(__name__)

def get_user_location(request):
    """
    Extract user location from request headers or form data.
    
    Args:
        request: Flask request object
        
    Returns:
        dict: Dictionary containing latitude and longitude, or None if not available
    """
    try:
        # Try to get location from form data (for web requests)
        latitude = request.form.get('latitude') or request.args.get('latitude')
        longitude = request.form.get('longitude') or request.args.get('longitude')
        
        if latitude and longitude:
            return {
                'latitude': float(latitude),
                'longitude': float(longitude)
            }
        
        # Try to get location from headers (for API requests)
        latitude = request.headers.get('X-Latitude')
        longitude = request.headers.get('X-Longitude')
        
        if latitude and longitude:
            return {
                'latitude': float(latitude),
                'longitude': float(longitude)
            }
        
        return None
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing location data: {str(e)}")
        return None

def is_user_in_office(request):
    """
    Check if user is within any valid office location.
    
    Args:
        request: Flask request object
        
    Returns:
        bool: True if user is in a valid office location, False otherwise
    """
    user_location = get_user_location(request)
    
    if not user_location:
        logger.warning("No location data provided in request")
        return False
    
    # Get all active office locations
    office_locations = OfficeLocation.query.filter_by(is_active=True).all()
    
    if not office_locations:
        logger.warning("No active office locations configured")
        return False
    
    # Check if user is within range of any office location
    for office in office_locations:
        if office.is_within_range(user_location['latitude'], user_location['longitude']):
            logger.info(f"User is within range of office: {office.name}")
            return True
    
    logger.warning(f"User location ({user_location['latitude']}, {user_location['longitude']}) is not within any office location")
    return False

def get_nearest_office(request):
    """
    Get the nearest office location to the user.
    
    Args:
        request: Flask request object
        
    Returns:
        OfficeLocation: Nearest office location, or None if no location data
    """
    user_location = get_user_location(request)
    
    if not user_location:
        return None
    
    office_locations = OfficeLocation.query.filter_by(is_active=True).all()
    
    if not office_locations:
        return None
    
    nearest_office = None
    nearest_distance = float('inf')
    
    for office in office_locations:
        distance = calculate_distance(
            user_location['latitude'],
            user_location['longitude'],
            office.latitude,
            office.longitude
        )
        
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_office = office
    
    return nearest_office

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using the Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        float: Distance in meters
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth's radius in meters
    r = 6371000
    
    return c * r

def validate_location_for_clearance(user_location, required_clearance_level):
    """
    Validate if user location allows access based on clearance level.
    
    Args:
        user_location: Dictionary with latitude and longitude
        required_clearance_level: Required clearance level enum
        
    Returns:
        bool: True if location allows access for clearance level
    """
    if not user_location:
        return False
    
    # Get office locations that match the required clearance level
    valid_offices = OfficeLocation.query.filter(
        OfficeLocation.is_active == True,
        OfficeLocation.required_clearance_level == required_clearance_level
    ).all()
    
    for office in valid_offices:
        if office.is_within_range(user_location['latitude'], user_location['longitude']):
            return True
    
    return False

def get_location_info(request):
    """
    Get comprehensive location information for logging.
    
    Args:
        request: Flask request object
        
    Returns:
        dict: Location information including IP, user agent, and GPS coordinates
    """
    user_location = get_user_location(request)
    
    location_info = {
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string if request.user_agent else None,
        'latitude': user_location['latitude'] if user_location else None,
        'longitude': user_location['longitude'] if user_location else None,
        'is_valid_location': is_user_in_office(request),
        'nearest_office': None
    }
    
    if user_location:
        nearest_office = get_nearest_office(request)
        if nearest_office:
            location_info['nearest_office'] = nearest_office.name
    
    return location_info
