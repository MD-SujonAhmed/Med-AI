# permissions.py
from rest_framework.permissions import BasePermission

class IsNormalUser(BasePermission):
    """
    Allow only authenticated non-superusers
    """
    def has_permission(self, request, view):
        user = request.user
        return (
            user and
            user.is_authenticated and
            not user.is_superuser
        )
        

class IsAdminOrSuperUser(BasePermission):
    """
    Allow only superusers
    """
    def has_permission(self, request, view):
        user = request.user
        return (
            user and
            user.is_authenticated and
            user.is_superuser
        )