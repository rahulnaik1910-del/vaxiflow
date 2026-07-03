from django.urls import path

from . import views


urlpatterns = [

    path(
        "run/<int:protein_id>/",
        views.run_blast,
        name="run_blast",
    ),

    path(
        "results/<int:protein_id>/",
        views.blast_results,
        name="blast_results",
    ),

]
