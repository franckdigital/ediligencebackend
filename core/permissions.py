from rest_framework.permissions import BasePermission

import logging
logger = logging.getLogger(__name__)
try:
    fh = logging.FileHandler('/etc/home/user/ediligencebackend/ediligence_permissions.log', mode='a')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    print('[IsProfileAdmin] FileHandler created in /etc/home/user/ediligencebackend/ediligence_permissions.log')
except Exception as e:
    print(f'[IsProfileAdmin] ERROR creating FileHandler: {e}')

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    """
    def has_permission(self, request, view):
        raise Exception("TEST CRASH PERMISSION")
        user = request.user
        logger.error(f"[IsProfileAdmin-ERROR] User: {user} - Authenticated: {user.is_authenticated}")
        if hasattr(user, 'profile'):
            logger.error(f"[IsProfileAdmin-ERROR] Profile role: {user.profile.role}")
        else:
            logger.error("[IsProfileAdmin-ERROR] Pas de profil lié!")
        print(f"[IsProfileAdmin-PRINT] User: {user} - Authenticated: {user.is_authenticated}")
        if hasattr(user, 'profile'):
            print(f"[IsProfileAdmin-PRINT] Profile role: {user.profile.role}")
        else:
            print("[IsProfileAdmin-PRINT] Pas de profil lié!")
        try:
            with open('/etc/home/user/ediligencebackend/ediligence_debug.txt', 'a') as f:
                f.write(f"User: {user}, Auth: {user.is_authenticated}\n")
                if hasattr(user, 'profile'):
                    f.write(f"Profile role: {user.profile.role}\n")
                else:
                    f.write("Pas de profil lié!\n")
        except Exception as e:
            print(f"[IsProfileAdmin] ERROR writing debug file: {e}")
        return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'ADMIN'
