from django.contrib import admin
from .models import Project, Genome, Analysis


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_name",
        "organism",
        "created_at",
    )


@admin.register(Genome)
class GenomeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "genome_file",
        "uploaded_at",
    )


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "analysis_type",
        "status",
        "started_at",
    )

    list_filter = (
        "analysis_type",
        "status",
    )
    