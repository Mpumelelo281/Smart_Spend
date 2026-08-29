"""
Rule 9: "Role-based access control checked server-side on every request,
not only in the interface." Every non-public endpoint in the project must
declare one of these — the client's UI hiding a button is a UX nicety, not
an access control.
"""

from rest_framework.permissions import BasePermission

from .models import User


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.STUDENT)


class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Role.ADMINISTRATOR
        )


class IsStudentServicesOfficer(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.STUDENT_SERVICES
        )


class IsAdministratorOrStudentServices(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.ADMINISTRATOR, User.Role.STUDENT_SERVICES)
        )
