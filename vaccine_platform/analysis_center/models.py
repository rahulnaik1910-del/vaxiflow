from django.db import models

from users.models import Project


class AnalysisModule(models.Model):
    """
    Represents one analysis module available
    inside a project.
    """

    STATUS_CHOICES = [
        ("ready", "Ready"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("waiting", "Waiting"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="analysis_modules",
    )

    module_name = models.CharField(
        max_length=100,
    )

    display_name = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.project.project_name} - "
            f"{self.display_name}"
        )
    