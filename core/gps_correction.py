"""
Utilitaire de correction GPS pour e-Diligence
Corrige automatiquement les coordonnées GPS aberrantes
"""
from .models import Bureau
import logging

logger = logging.getLogger(__name__)

def is_valid_ivory_coast_coordinates(latitude, longitude):
    """
    Vérifie si les coordonnées sont dans les limites de la Côte d'Ivoire
    Côte d'Ivoire: Latitude 4°-11°N, Longitude 9°W-0°E
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        # Limites approximatives de la Côte d'Ivoire
        return (4.0 <= lat <= 11.0) and (-9.0 <= lon <= 0.0)
    except (ValueError, TypeError):
        return False

def correct_gps_coordinates(latitude, longitude, user=None):
    """
    Corrige automatiquement les coordonnées GPS aberrantes
    
    Args:
        latitude: Latitude reçue du GPS
        longitude: Longitude reçue du GPS
        user: Utilisateur (optionnel, pour récupérer son bureau)
    
    Returns:
        dict: {
            'latitude': float,
            'longitude': float,
            'corrected': bool,
            'message': str
        }
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        # Vérifier si les coordonnées sont valides
        if is_valid_ivory_coast_coordinates(lat, lon):
            return {
                'latitude': lat,
                'longitude': lon,
                'corrected': False,
                'message': 'Coordonnées GPS valides'
            }
        
        # Coordonnées aberrantes détectées - correction nécessaire
        logger.warning(f"Coordonnées GPS aberrantes détectées: {lat}, {lon}")
        
        # Récupérer les coordonnées du bureau par défaut
        bureau = None
        if user and hasattr(user, 'agent_profile') and user.agent_profile.bureau:
            bureau = user.agent_profile.bureau
        else:
            bureau = Bureau.objects.first()
        
        if bureau:
            corrected_lat = float(bureau.latitude_centre)
            corrected_lon = float(bureau.longitude_centre)
            
            logger.info(f"Correction GPS appliquée: {lat},{lon} -> {corrected_lat},{corrected_lon}")
            
            return {
                'latitude': corrected_lat,
                'longitude': corrected_lon,
                'corrected': True,
                'message': f'Position GPS corrigée automatiquement vers le bureau {bureau.nom}'
            }
        else:
            # Coordonnées par défaut pour Abidjan si aucun bureau
            default_lat = 5.396534
            default_lon = -3.981635
            
            logger.info(f"Correction GPS par défaut appliquée: {lat},{lon} -> {default_lat},{default_lon}")
            
            return {
                'latitude': default_lat,
                'longitude': default_lon,
                'corrected': True,
                'message': 'Position GPS corrigée vers les coordonnées par défaut (Abidjan)'
            }
            
    except (ValueError, TypeError) as e:
        logger.error(f"Erreur lors de la correction GPS: {e}")
        
        # Coordonnées par défaut en cas d'erreur
        bureau = Bureau.objects.first()
        if bureau:
            return {
                'latitude': float(bureau.latitude_centre),
                'longitude': float(bureau.longitude_centre),
                'corrected': True,
                'message': 'Coordonnées GPS invalides - correction appliquée'
            }
        else:
            return {
                'latitude': 5.396534,
                'longitude': -3.981635,
                'corrected': True,
                'message': 'Coordonnées GPS invalides - coordonnées par défaut appliquées'
            }

def get_common_problematic_coordinates():
    """
    Retourne une liste des coordonnées GPS problématiques communes
    """
    return [
        (37.421998, -122.084000, "Californie (émulateur Android)"),
        (37.4220936, -122.083922, "Californie (émulateur iOS)"),
        (0.0, 0.0, "Coordonnées nulles"),
        (51.505, -0.09, "Londres (défaut)"),
        (40.7128, -74.0060, "New York (défaut)"),
    ]

def detect_problematic_gps(latitude, longitude):
    """
    Détecte si les coordonnées correspondent à des positions problématiques connues
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        for prob_lat, prob_lon, description in get_common_problematic_coordinates():
            # Tolérance de 0.001 degré (environ 100m)
            if abs(lat - prob_lat) < 0.001 and abs(lon - prob_lon) < 0.001:
                return True, description
                
        return False, None
        
    except (ValueError, TypeError):
        return True, "Coordonnées invalides"
