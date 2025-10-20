from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list"),
    path("preferences/", views.NotificationPreferenceUpdateView.as_view(), name="preferences"),
    path("<int:pk>/read/", views.mark_notification_read, name="mark-read"),
]
