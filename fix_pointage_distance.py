#!/usr/bin/env python
"""
Script pour corriger la validation de distance dans le système de pointage
"""

def fix_presence_viewset():
    """Corriger le PresenceViewSet pour utiliser les coordonnées du Bureau"""
    
    corrections = """
    CORRECTIONS À APPLIQUER MANUELLEMENT dans core/views.py :
    
    1. Ligne ~1198-1210 : Remplacer la validation GPS par :
    
    # Validation GPS par rapport au bureau
    from .models import Bureau
    bureau = agent_obj.bureau if agent_obj.bureau else Bureau.objects.filter(nom__icontains='Principal').first()
    if not bureau:
        bureau = Bureau.objects.first()  # Fallback sur le premier bureau
        
    if bureau and bureau.latitude_centre and bureau.longitude_centre:
        try:
            lat1 = float(latitude)
            lon1 = float(longitude)
            lat2 = float(bureau.latitude_centre)
            lon2 = float(bureau.longitude_centre)
            rayon = float(bureau.rayon_metres) if bureau.rayon_metres else 100.0  # Rayon configurable
    
    2. Ligne ~1223-1231 : Remplacer la validation de distance par :
    
            distance = haversine(lat1, lon1, lat2, lon2)
            logger.info('[PresenceViewSet] Distance: %.1f m par rapport au bureau %s, Rayon: %.1f m', 
                       distance, bureau.nom, rayon)
            
            if distance > rayon:
                logger.warning('[PresenceViewSet] Hors zone autorisée: %.1f m > %.1f m', distance, rayon)
                raise ValidationError({
                    'error': f'Vous êtes trop loin du bureau {bureau.nom} pour pointer ({distance:.1f}m > {rayon:.1f}m).',
                    'distance': round(distance, 1),
                    'rayon_autorise': rayon,
                    'bureau': bureau.nom
                })
            localisation_valide = True
    
    3. Ligne ~1236 : Changer le message d'avertissement :
    
        else:
            commentaire_final += f" [Avertissement : aucune configuration GPS trouvée pour le bureau.]"
    """
    
    print(corrections)

if __name__ == "__main__":
    fix_presence_viewset()
