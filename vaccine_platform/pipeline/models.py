from django.db import models


class Workflow(models.Model):
    """
    Defines a workflow template.
    Example:
        Reverse Vaccinology
        RNA-Seq
        Comparative Genomics
    """

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    version = models.CharField(max_length=20, default="1.0")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkflowStage(models.Model):
    """
    Defines one stage inside a workflow.
    """

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="stages"
    )

    order = models.PositiveIntegerField()

    name = models.CharField(max_length=200)

    tool_name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("workflow", "order")

    def __str__(self):
        return f"{self.order}. {self.name}"
    