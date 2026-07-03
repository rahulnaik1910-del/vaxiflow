from django.contrib import admin

from .models import BlastResult


@admin.register(BlastResult)
class BlastResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "subject_id",
        "identity",
        "evalue",
        "bit_score",
    )

    search_fields = (
        "protein__protein_id",
        "subject_id",
    )

    list_filter = (
        "created_at",
    )
    