from rest_framework.permissions import BasePermission

import logging
logger = logging.getLogger(__name__)

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    """
    def has_permission(self, request, view):
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
        return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'ADMIN'
