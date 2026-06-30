from django.contrib import admin
from .models import Protein


@admin.register(Protein)
class ProteinAdmin(admin.ModelAdmin):

    list_display = (
        "protein_id",
        "gene",
        "product",
        "length",
        "analysis",
    )

    search_fields = (
        "protein_id",
        "gene",
        "product",
    )

    list_filter = (
        "analysis",
    )
    