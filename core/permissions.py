from rest_framework.permissions import BasePermission

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    Django superusers always pass regardless of profile role.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, 'profile', None)
        if not profile:
            return False
        role = getattr(profile, 'role', None)
        allowed_roles = ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']
        return role in allowed_roles