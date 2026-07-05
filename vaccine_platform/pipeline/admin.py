from django.contrib import admin
from .models import Workflow, WorkflowStage


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "version",
        "is_active",
        "created_at",
    )

    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = (
        "workflow",
        "order",
        "name",
        "tool_name",
        "enabled",
    )

    list_filter = (
        "workflow",
        "enabled",
    )

    ordering = ("workflow", "order")
    