from rest_framework.permissions import BasePermission

import logging
logger = logging.getLogger(__name__)

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    """
    def has_permission(self, request, view):
        user = request.user
        logger.info(f"[IsProfileAdmin] User: {user} - Authenticated: {user.is_authenticated}")
        if hasattr(user, 'profile'):
            logger.info(f"[IsProfileAdmin] Profile role: {user.profile.role}")
        else:
            logger.info("[IsProfileAdmin] Pas de profil lié!")
        return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'ADMIN'
