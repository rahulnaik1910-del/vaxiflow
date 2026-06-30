from django.urls import path
from . import views

urlpatterns = [

    path(
        "analysis/<int:analysis_id>/",
        views.protein_list,
        name="protein_list",
    ),

    path(
        "<int:protein_id>/",
        views.protein_detail,
        name="protein_detail",
    ),

]
