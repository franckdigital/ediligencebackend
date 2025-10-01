#!/usr/bin/env python
"""
Script pour appliquer automatiquement les corrections de pointage
"""
import re

def apply_fixes():
    """Appliquer les corrections dans core/views.py"""
    
    # Lire le fichier
    with open('core/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Correction 1: Remplacer le message d'avertissement (ligne ~1236)
    old_warning = 'commentaire_final += " [Avertissement : aucune configuration GPS de zone autorisée sur votre profil Agent.]"'
    new_warning = 'commentaire_final += " [Avertissement : aucune configuration GPS trouvée pour le bureau.]"'
    content = content.replace(old_warning, new_warning)
    
    # Correction 2: Supprimer la duplication dans la validation de distance
    # Pattern pour trouver la section dupliquée
    pattern = r'(distance = haversine\(lat1, lon1, lat2, lon2\)\s+if distance > rayon:\s+logger\.warning\(\'\[PresenceViewSet\] Hors zone autorisée: %.1f m > %.1f m\', distance, rayon\)\s+raise ValidationError\(\{\'error\': f\'Vous êtes hors de la zone autorisée pour l\'enregistrement de présence \(\{distance:.1f\} m > \{rayon:.1f\} m\)\. Veuillez vous rapprocher de votre bureau\.\'\}\)\s+logger\.warning\(\'\[PresenceViewSet\] Distance calculée: %s m\', distance\)\s+if distance > rayon:\s+logger\.warning\(\'\[PresenceViewSet\] Hors zone autorisée: %.1f m > %.1f m\', distance, rayon\)\s+raise ValidationError\(f"Vous êtes hors de la zone autorisée \(\{distance:.1f\} m > \{rayon:.1f\} m\)"\)\s+localisation_valide = True)'
    
    replacement = '''distance = haversine(lat1, lon1, lat2, lon2)
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
                localisation_valide = True'''
    
    # Recherche et remplacement plus simple ligne par ligne
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Détecter le début de la section à remplacer
        if 'distance = haversine(lat1, lon1, lat2, lon2)' in line:
            # Remplacer toute la section problématique
            new_lines.append('                distance = haversine(lat1, lon1, lat2, lon2)')
            new_lines.append("                logger.info('[PresenceViewSet] Distance: %.1f m par rapport au bureau %s, Rayon: %.1f m',")
            new_lines.append("                           distance, bureau.nom, rayon)")
            new_lines.append("                ")
            new_lines.append("                if distance > rayon:")
            new_lines.append("                    logger.warning('[PresenceViewSet] Hors zone autorisée: %.1f m > %.1f m', distance, rayon)")
            new_lines.append("                    raise ValidationError({")
            new_lines.append("                        'error': f'Vous êtes trop loin du bureau {bureau.nom} pour pointer ({distance:.1f}m > {rayon:.1f}m).',")
            new_lines.append("                        'distance': round(distance, 1),")
            new_lines.append("                        'rayon_autorise': rayon,")
            new_lines.append("                        'bureau': bureau.nom")
            new_lines.append("                    })")
            new_lines.append("                localisation_valide = True")
            
            # Ignorer les lignes suivantes jusqu'à localisation_valide = True
            i += 1
            while i < len(lines) and 'localisation_valide = True' not in lines[i]:
                i += 1
            # Ignorer aussi la ligne localisation_valide = True car on l'a déjà ajoutée
            if i < len(lines) and 'localisation_valide = True' in lines[i]:
                i += 1
            continue
        else:
            new_lines.append(lines[i])
        
        i += 1
    
    # Écrire le fichier corrigé
    with open('core/views.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Corrections appliquées avec succès !")
    print("📋 Corrections effectuées :")
    print("  1. ✅ Message d'avertissement corrigé")
    print("  2. ✅ Duplication dans la validation de distance supprimée")
    print("  3. ✅ Messages d'erreur améliorés avec nom du bureau")
    print("  4. ✅ Informations de debug ajoutées")

if __name__ == "__main__":
    apply_fixes()
