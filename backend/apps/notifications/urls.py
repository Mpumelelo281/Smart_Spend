from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list"),
    path("mark-all-read/", views.MarkAllNotificationsReadView.as_view(), name="mark-all-read"),
    path("<uuid:notification_id>/read/", views.MarkNotificationReadView.as_view(), name="mark-read"),
]
