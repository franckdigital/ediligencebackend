#!/usr/bin/env python
"""
Script de test pour le système de verrouillage d'appareil
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import DeviceLock, User
from django.utils import timezone

def test_device_locking():
    print("=" * 60)
    print("TEST DU SYSTÈME DE VERROUILLAGE D'APPAREIL")
    print("=" * 60)
    
    # 1. Vérifier que le modèle existe
    print("\n1. Vérification du modèle DeviceLock...")
    try:
        count = DeviceLock.objects.count()
        print(f"   ✅ Modèle DeviceLock accessible ({count} entrées)")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 2. Créer un verrouillage de test
    print("\n2. Création d'un verrouillage de test...")
    try:
        user = User.objects.first()
        if not user:
            print("   ❌ Aucun utilisateur trouvé")
            return
        
        device_id = f"test-device-{timezone.now().timestamp()}"
        lock = DeviceLock.objects.create(
            device_id=device_id,
            user=user,
            username=user.username,
            email=user.email
        )
        print(f"   ✅ Verrouillage créé: {lock}")
        
        # 3. Vérifier le verrouillage
        print("\n3. Vérification du verrouillage...")
        found_lock = DeviceLock.objects.filter(device_id=device_id).first()
        if found_lock:
            print(f"   ✅ Verrouillage trouvé: {found_lock.device_id} → {found_lock.username}")
        else:
            print("   ❌ Verrouillage non trouvé")
        
        # 4. Tester la mise à jour
        print("\n4. Test de mise à jour...")
        found_lock.last_used = timezone.now()
        found_lock.save()
        print(f"   ✅ Dernière utilisation mise à jour: {found_lock.last_used}")
        
        # 5. Supprimer le test
        print("\n5. Nettoyage...")
        found_lock.delete()
        print("   ✅ Verrouillage de test supprimé")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Afficher tous les verrouillages existants
    print("\n6. Verrouillages existants:")
    locks = DeviceLock.objects.all()
    if locks.exists():
        for lock in locks:
            print(f"   - {lock.device_id} → {lock.username} ({lock.email})")
            print(f"     Verrouillé: {lock.locked_at}, Dernière utilisation: {lock.last_used}")
    else:
        print("   Aucun verrouillage actif")
    
    print("\n" + "=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)

if __name__ == '__main__':
    test_device_locking()
