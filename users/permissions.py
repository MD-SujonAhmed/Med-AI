from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Allow access only to users with role = admin
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )
