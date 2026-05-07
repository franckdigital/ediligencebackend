from rest_framework.permissions import BasePermission

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        profile = getattr(user, 'profile', None)
        if not profile:
            return False
            
        role = getattr(profile, 'role', None)
        print("DEBUG IsProfileAdmin: user=", user, "role=", role)
        
        # Permettre l'accès aux ADMIN, SUPERIEUR et DIRECTEUR
        allowed_roles = ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']
        return role in allowed_roles