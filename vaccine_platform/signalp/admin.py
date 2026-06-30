from django.contrib import admin

from .models import SignalPResult


@admin.register(SignalPResult)
class SignalPResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "prediction",
        "probability",
        "cleavage_site",
        "version",
    )

    search_fields = (
        "protein__protein_id",
        "prediction",
    )

    list_filter = (
        "prediction",
        "version",
    )
    