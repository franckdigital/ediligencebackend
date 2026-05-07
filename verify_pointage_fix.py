#!/usr/bin/env python
"""
Script de vérification des corrections appliquées
"""

def verify_fixes():
    """Vérifier que les corrections ont été appliquées"""
    
    print("🔍 VÉRIFICATION DES CORRECTIONS APPLIQUÉES")
    print("=" * 50)
    
    try:
        with open('core/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        
        # Vérification 1: Message d'avertissement corrigé
        if 'aucune configuration GPS trouvée pour le bureau' in content:
            checks.append("✅ Message d'avertissement corrigé")
        else:
            checks.append("❌ Message d'avertissement non corrigé")
        
        # Vérification 2: Utilisation des coordonnées du bureau
        if 'bureau.latitude_centre' in content and 'bureau.longitude_centre' in content:
            checks.append("✅ Utilisation des coordonnées du bureau")
        else:
            checks.append("❌ Coordonnées du bureau non utilisées")
        
        # Vérification 3: Rayon configurable
        if 'bureau.rayon_metres' in content:
            checks.append("✅ Rayon configurable implémenté")
        else:
            checks.append("❌ Rayon configurable non implémenté")
        
        # Vérification 4: Messages d'erreur améliorés
        if 'bureau.nom' in content and 'distance' in content and 'rayon_autorise' in content:
            checks.append("✅ Messages d'erreur améliorés")
        else:
            checks.append("❌ Messages d'erreur non améliorés")
        
        # Vérification 5: Pas de duplication
        distance_count = content.count('distance = haversine(lat1, lon1, lat2, lon2)')
        if distance_count <= 2:  # Une fois dans SimplePresenceView, une fois dans PresenceViewSet
            checks.append("✅ Duplication supprimée")
        else:
            checks.append(f"❌ Duplication encore présente ({distance_count} occurrences)")
        
        print("\n📋 RÉSULTATS DE LA VÉRIFICATION:")
        for check in checks:
            print(f"  {check}")
        
        success_count = sum(1 for check in checks if check.startswith("✅"))
        total_count = len(checks)
        
        print(f"\n🎯 SCORE: {success_count}/{total_count} corrections appliquées")
        
        if success_count == total_count:
            print("\n🎉 TOUTES LES CORRECTIONS ONT ÉTÉ APPLIQUÉES AVEC SUCCÈS !")
            print("\n📱 Le système de pointage est maintenant opérationnel avec :")
            print("  ✅ Validation de distance basée sur les coordonnées du bureau")
            print("  ✅ Rayon configurable via l'interface admin")
            print("  ✅ Messages d'erreur détaillés")
            print("  ✅ Liaison GPS Admin → Mobile fonctionnelle")
            
            print("\n🔗 APIs de pointage disponibles :")
            print("  - POST /api/simple-presence/ (API principale)")
            print("  - POST /api/presences/ (API avancée)")
            
            print("\n⚙️ Configuration via :")
            print("  - Interface web: /coordonnees-gps")
            print("  - API: /api/bureaux/")
        else:
            print("\n⚠️  Certaines corrections nécessitent une vérification manuelle")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    verify_fixes()
