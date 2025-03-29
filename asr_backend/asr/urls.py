from django.urls import path
from . import views

urlpatterns = [
    # path("task", views.create_task),
    # path("task/<str:task_id>", views.get_task),
    path("status", views.health_check),
]
