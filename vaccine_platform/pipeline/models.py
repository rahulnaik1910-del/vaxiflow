from django.db import models
from users.models import Project


class Workflow(models.Model):
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

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="stages",
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


class WorkflowRun(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="workflow_runs",
    )

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="runs",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    progress = models.PositiveIntegerField(default=0)

    current_stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.project.project_name} - Run #{self.pk}"


class WorkflowTask(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    workflow_run = models.ForeignKey(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    log = models.TextField(blank=True)

    exit_code = models.IntegerField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["stage__order"]
        unique_together = ("workflow_run", "stage")

    def __str__(self):
        return (
            f"{self.workflow_run.project.project_name} - "
            f"{self.stage.name}"
        )


class Protein(models.Model):

    workflow_run = models.ForeignKey(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name="proteins",
    )

    protein_id = models.CharField(max_length=200)

    locus_tag = models.CharField(
        max_length=200,
        blank=True,
    )

    gene = models.CharField(
        max_length=200,
        blank=True,
    )

    product = models.CharField(
        max_length=500,
        blank=True,
    )

    sequence = models.TextField()

    length = models.IntegerField()

    start = models.IntegerField(
        null=True,
        blank=True,
    )

    end = models.IntegerField(
        null=True,
        blank=True,
    )

    strand = models.CharField(
        max_length=1,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["protein_id"]

    def __str__(self):
        if self.product:
            return f"{self.protein_id} ({self.product})"
        return self.protein_id
    