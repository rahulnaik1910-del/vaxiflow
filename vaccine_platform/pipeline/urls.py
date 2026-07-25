from django.urls import path

from . import views

urlpatterns = [

    path(
        "start/<int:project_id>/",
        views.start_workflow,
        name="start_workflow",
    ),

    path(
        "report/<int:project_id>/",
        views.candidate_report,
        name="candidate_report",
    ),

    path(
        "report/candidate/<int:ranking_id>/",
        views.candidate_detail,
        name="candidate_detail",
    ),

]
