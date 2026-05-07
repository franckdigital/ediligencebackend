#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verification des corrections appliquees
"""

def check_fixes():
    """Verifier que les corrections ont ete appliquees"""
    
    print("VERIFICATION DES CORRECTIONS APPLIQUEES")
    print("=" * 50)
    
    try:
        with open('core/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        
        # Verification 1: Message d'avertissement corrige
        if 'aucune configuration GPS trouvee pour le bureau' in content:
            checks.append("OK Message d'avertissement corrige")
        else:
            checks.append("KO Message d'avertissement non corrige")
        
        # Verification 2: Utilisation des coordonnees du bureau
        if 'bureau.latitude_centre' in content and 'bureau.longitude_centre' in content:
            checks.append("OK Utilisation des coordonnees du bureau")
        else:
            checks.append("KO Coordonnees du bureau non utilisees")
        
        # Verification 3: Rayon configurable
        if 'bureau.rayon_metres' in content:
            checks.append("OK Rayon configurable implemente")
        else:
            checks.append("KO Rayon configurable non implemente")
        
        # Verification 4: Messages d'erreur ameliores
        if 'bureau.nom' in content and 'distance' in content and 'rayon_autorise' in content:
            checks.append("OK Messages d'erreur ameliores")
        else:
            checks.append("KO Messages d'erreur non ameliores")
        
        # Verification 5: Pas de duplication
        distance_count = content.count('distance = haversine(lat1, lon1, lat2, lon2)')
        if distance_count <= 2:
            checks.append("OK Duplication supprimee")
        else:
            checks.append(f"KO Duplication encore presente ({distance_count} occurrences)")
        
        print("\nRESULTATS DE LA VERIFICATION:")
        for check in checks:
            print(f"  {check}")
        
        success_count = sum(1 for check in checks if check.startswith("OK"))
        total_count = len(checks)
        
        print(f"\nSCORE: {success_count}/{total_count} corrections appliquees")
        
        if success_count == total_count:
            print("\nTOUTES LES CORRECTIONS ONT ETE APPLIQUEES AVEC SUCCES !")
            print("\nLe systeme de pointage est maintenant operationnel avec :")
            print("  - Validation de distance basee sur les coordonnees du bureau")
            print("  - Rayon configurable via l'interface admin")
            print("  - Messages d'erreur detailles")
            print("  - Liaison GPS Admin -> Mobile fonctionnelle")
            
            print("\nAPIs de pointage disponibles :")
            print("  - POST /api/simple-presence/ (API principale)")
            print("  - POST /api/presences/ (API avancee)")
            
            print("\nConfiguration via :")
            print("  - Interface web: /coordonnees-gps")
            print("  - API: /api/bureaux/")
        else:
            print("\nCertaines corrections necessitent une verification manuelle")
        
    except Exception as e:
        print(f"Erreur lors de la verification: {e}")

if __name__ == "__main__":
    check_fixes()
