from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("ask/", views.AssistantAskView.as_view(), name="ask"),
]
