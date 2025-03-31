from django.urls import path

from . import views

urlpatterns = [
    path("task", views.TranscribeView.as_view(), name="create_task"),
    path("task/<str:task_id>", views.TranscribeView.as_view(), name="get_task"),
    path("", views.health_check),
]
