from rest_framework.permissions import BasePermission

from kyc.models import UserRole


class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == UserRole.REVIEWER)


class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == UserRole.MERCHANT)
