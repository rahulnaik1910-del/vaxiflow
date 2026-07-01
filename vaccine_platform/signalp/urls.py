from django.urls import path

from . import views


urlpatterns = [

    path(
        "run/<int:analysis_id>/",
        views.run_signalp,
        name="run_signalp",
    ),

    path(
        "results/<int:analysis_id>/",
        views.signalp_results,
        name="signalp_results",
    ),

]
