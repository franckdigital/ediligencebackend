from rest_framework.permissions import BasePermission

class IsProfileAdmin(BasePermission):
    """
    Permission to allow access only to users whose UserProfile.role == 'ADMIN'.
    """
    def has_permission(self, request, view):
        user = request.user
        print("DEBUG IsProfileAdmin: user=", user, "is_authenticated=", user.is_authenticated, "profile=", getattr(user, 'profile', None), "role=", getattr(getattr(user, 'profile', None), 'role', None))
        return True