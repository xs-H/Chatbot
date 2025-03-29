from django.urls import path

from . import views

urlpatterns = [
    path("task", views.TranscribeView.as_view(), name="transcribe"),
    path("status", views.health_check),
]
