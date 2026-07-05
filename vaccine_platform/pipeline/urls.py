from django.urls import path

from . import views

urlpatterns = [

    path(
        "start/<int:project_id>/",
        views.start_workflow,
        name="start_workflow",
    ),

]
