from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "projects/create/",
        views.create_project,
        name="create_project",
    ),

    path(
        "projects/<int:project_id>/",
        views.project_detail,
        name="project_detail",
    ),

    path(
        "projects/<int:project_id>/upload/",
        views.upload_genome,
        name="upload_genome",
    ),

    path(
        "genome/<int:genome_id>/download/",
        views.download_genome,
        name="download_genome",
    ),

    path(
        "genome/<int:genome_id>/annotate/",
        views.run_annotation,
        name="run_annotation",
    ),
]
