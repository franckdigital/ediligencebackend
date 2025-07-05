from rest_framework.permissions import BasePermission

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'ADMIN'
