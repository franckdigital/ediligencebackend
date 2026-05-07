# Commandes pour forcer la mise à jour de TOUS les bureaux
# Utilisez: python manage.py shell < force_update_shell.py

from core.models import Bureau
from decimal import Decimal

print("🔧 MISE À JOUR FORCÉE DE TOUS LES BUREAUX")
print("=" * 50)

# Nouvelles coordonnées correctes
new_lat = Decimal('5.396534')
new_lon = Decimal('-3.981554')
new_rayon = 200

print(f"📍 Nouvelles coordonnées: {new_lat}, {new_lon}")
print(f"🎯 Nouveau rayon: {new_rayon}m")

# Mettre à jour TOUS les bureaux
bureaux = Bureau.objects.all()
print(f"\n🏢 Bureaux trouvés: {bureaux.count()}")

for bureau in bureaux:
    print(f"\n   Bureau: {bureau.nom}")
    print(f"   Anciennes coords: {bureau.latitude_centre}, {bureau.longitude_centre}")
    
    # Mise à jour
    bureau.latitude_centre = new_lat
    bureau.longitude_centre = new_lon
    bureau.rayon_metres = new_rayon
    bureau.save()
    
    print(f"   ✅ Nouvelles coords: {bureau.latitude_centre}, {bureau.longitude_centre}")
    print(f"   ✅ Nouveau rayon: {bureau.rayon_metres}m")

print(f"\n🎉 SUCCÈS!")
print(f"✅ {bureaux.count()} bureau(x) mis à jour")
print("📱 Testez maintenant le pointage mobile")

# Vérification finale
print(f"\n🔍 VÉRIFICATION FINALE:")
for bureau in Bureau.objects.all():
    print(f"   {bureau.nom}: {bureau.latitude_centre}, {bureau.longitude_centre} ({bureau.rayon_metres}m)")
