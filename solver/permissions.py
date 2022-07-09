from rest_framework import permissions

from solver.models import DayPreference


class DayPreferenceChangePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, DayPreference):
            return obj.user_preferences.user == request.user

        return True
