from django.urls import path

from . import views


urlpatterns = [

    path(
        "<int:project_id>/",
        views.analysis_dashboard,
        name="analysis_dashboard",
    ),

]
