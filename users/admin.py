from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Users, UserProfile

class UserAdmin(BaseUserAdmin):
    list_display = ('full_name', 'email', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'full_name')
    ordering = ('email',)

    # Field sets for user detail/edit page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    # Field sets for creating new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_staff', 'is_active', 'is_superuser')}
        ),
    )

    filter_horizontal = ('groups', 'user_permissions',)

# Register the custom user model with the admin
admin.site.register(Users, UserAdmin)
