from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = NotificationSerializer
    # A bare array, not the project's default paginated envelope — the
    # queryset below is already capped at 50, and the frontend bell
    # dropdown wants a plain list to render directly.
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(profile__user=self.request.user).order_by("-created_at")[:50]


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification, notification_id=notification_id, profile__user=request.user
        )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request):
        Notification.objects.filter(profile__user=request.user, is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
