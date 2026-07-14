"""
Utilitaires pour les calculs de géofencing et géolocalisation
"""
import math
from decimal import Decimal

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculer la distance entre deux points GPS en utilisant la formule de Haversine
    
    Args:
        lat1, lon1: Latitude et longitude du premier point
        lat2, lon2: Latitude et longitude du second point
    
    Returns:
        float: Distance en mètres
    """
    # Convertir en float si ce sont des Decimal
    if isinstance(lat1, Decimal):
        lat1 = float(lat1)
    if isinstance(lon1, Decimal):
        lon1 = float(lon1)
    if isinstance(lat2, Decimal):
        lat2 = float(lat2)
    if isinstance(lon2, Decimal):
        lon2 = float(lon2)
    
    # Rayon de la Terre en mètres
    R = 6371000
    
    # Convertir les degrés en radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Différences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Formule de Haversine
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distance en mètres
    distance = R * c
    
    return distance

def is_within_geofence(agent_lat, agent_lon, center_lat, center_lon, radius_meters):
    """
    Vérifier si un agent est dans le périmètre autorisé
    
    Args:
        agent_lat, agent_lon: Position de l'agent
        center_lat, center_lon: Centre du géofence (bureau)
        radius_meters: Rayon autorisé en mètres
    
    Returns:
        tuple: (bool: dans le périmètre, float: distance en mètres)
    """
    distance = calculate_distance(agent_lat, agent_lon, center_lat, center_lon)
    is_within = distance <= radius_meters
    
    return is_within, distance

def get_distance_status(distance_meters, radius_meters):
    """
    Obtenir le statut basé sur la distance
    
    Args:
        distance_meters: Distance actuelle en mètres
        radius_meters: Rayon autorisé en mètres
    
    Returns:
        dict: Statut avec informations détaillées
    """
    if distance_meters <= radius_meters:
        status = "DANS_PERIMETRE"
        level = "success"
        message = f"Dans le périmètre autorisé ({distance_meters:.1f}m / {radius_meters}m)"
    elif distance_meters <= radius_meters * 1.5:
        status = "PROCHE_LIMITE"
        level = "warning"
        message = f"Proche de la limite ({distance_meters:.1f}m / {radius_meters}m)"
    else:
        status = "HORS_PERIMETRE"
        level = "danger"
        message = f"Hors du périmètre autorisé ({distance_meters:.1f}m / {radius_meters}m)"
    
    return {
        'status': status,
        'level': level,
        'message': message,
        'distance': distance_meters,
        'radius': radius_meters,
        'percentage': (distance_meters / radius_meters) * 100 if radius_meters > 0 else 0
    }

def format_distance(distance_meters):
    """
    Formater la distance pour l'affichage
    
    Args:
        distance_meters: Distance en mètres
    
    Returns:
        str: Distance formatée
    """
    if distance_meters < 1000:
        return f"{distance_meters:.1f}m"
    else:
        return f"{distance_meters / 1000:.2f}km"

def validate_coordinates(lat, lon):
    """
    Valider les coordonnées GPS
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        bool: True si les coordonnées sont valides
    """
    try:
        lat = float(lat)
        lon = float(lon)
        
        # Vérifier les limites géographiques
        if not (-90 <= lat <= 90):
            return False
        if not (-180 <= lon <= 180):
            return False
        
        return True
    except (ValueError, TypeError):
        return False

def get_gps_reference_for_user(user):
    """
    Résout le point de référence GPS (zone autorisée) d'un agent, avec la même
    priorité que la validation de pointage (voir PresenceViewSet.perform_create) :
      1. Palier actif du site (UserProfile.site) avec coordonnées GPS
      2. Coordonnées GPS directes du site
      3. Bureau de l'Agent (fallback)

    Args:
        user: instance django.contrib.auth.models.User

    Returns:
        dict {'latitude': float, 'longitude': float, 'rayon_metres': float, 'nom': str, 'bureau': Bureau|None}
        ou None si aucune référence GPS n'est configurée pour cet agent.
    """
    from .models import SitePalier

    user_profile = getattr(user, 'profile', None)
    user_site = getattr(user_profile, 'site', None) if user_profile else None
    agent_obj = getattr(user, 'agent_profile', None)
    bureau = getattr(agent_obj, 'bureau', None) if agent_obj else None

    if user_site:
        palier = SitePalier.objects.filter(
            site=user_site, est_actif=True,
            latitude__isnull=False, longitude__isnull=False
        ).order_by('ordre').first()
        if palier:
            return {
                'latitude': float(palier.latitude),
                'longitude': float(palier.longitude),
                'rayon_metres': float(palier.rayon_pointage),
                'nom': f"{user_site.nom} — {palier.nom}",
                'bureau': bureau,
            }
        if user_site.latitude and user_site.longitude:
            return {
                'latitude': float(user_site.latitude),
                'longitude': float(user_site.longitude),
                'rayon_metres': float(user_site.rayon_pointage),
                'nom': user_site.nom,
                'bureau': bureau,
            }

    if bureau and bureau.latitude_centre and bureau.longitude_centre:
        return {
            'latitude': float(bureau.latitude_centre),
            'longitude': float(bureau.longitude_centre),
            'rayon_metres': float(bureau.rayon_metres) if bureau.rayon_metres else 200.0,
            'nom': user_site.nom if user_site else bureau.nom,
            'bureau': bureau,
        }

    return None


def is_in_cote_divoire(lat, lon):
    """
    Vérifier si les coordonnées sont en Côte d'Ivoire (approximatif)
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        bool: True si les coordonnées semblent être en Côte d'Ivoire
    """
    try:
        lat = float(lat)
        lon = float(lon)
        
        # Limites approximatives de la Côte d'Ivoire
        # Latitude: 4° à 11° Nord
        # Longitude: 9° à 2° Ouest (donc -9 à -2)
        return (4 <= lat <= 11) and (-9 <= lon <= 0)
    except (ValueError, TypeError):
        return False
