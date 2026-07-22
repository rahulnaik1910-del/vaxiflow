from django.db import models
from users.models import Project, Genome
from proteins.models import Protein


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

    log = models.TextField(
        blank=True,
    )

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


class PanarooRun(models.Model):
    """
    One Panaroo pan-genome analysis for a single WorkflowRun.

    Unlike Bakta (which produces one Analysis per genome), Panaroo
    operates across every genome in the project at once, so this is
    a single record per WorkflowRun, not per genome.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    workflow_run = models.OneToOneField(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name="panaroo_run",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    genome_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of genomes included in this Panaroo run.",
    )

    core_gene_count = models.PositiveIntegerField(
        default=0,
    )

    accessory_gene_count = models.PositiveIntegerField(
        default=0,
    )

    output_directory = models.CharField(
        max_length=500,
        blank=True,
    )

    log = models.TextField(
        blank=True,
    )

    exit_code = models.IntegerField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.workflow_run.project.project_name} - "
            f"Panaroo Run #{self.pk}"
        )


class GeneCluster(models.Model):
    """
    One orthologous gene cluster identified by Panaroo, i.e. one row
    of gene_presence_absence.csv.
    """

    panaroo_run = models.ForeignKey(
        PanarooRun,
        on_delete=models.CASCADE,
        related_name="gene_clusters",
    )

    cluster_name = models.CharField(
        max_length=300,
        help_text="Panaroo's gene/cluster name, e.g. 'dnaA'.",
    )

    is_core = models.BooleanField(
        default=False,
        help_text=(
            "True if this gene is present in enough genomes to be "
            "considered part of the core genome."
        ),
    )

    genome_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of genomes in which this gene was found.",
    )

    class Meta:
        ordering = ["-is_core", "cluster_name"]

    def __str__(self):
        kind = "core" if self.is_core else "accessory"
        return f"{self.cluster_name} ({kind})"


class GeneClusterMember(models.Model):
    """
    Links a GeneCluster to the specific Protein (from a specific
    genome) that belongs to it.
    """

    gene_cluster = models.ForeignKey(
        GeneCluster,
        on_delete=models.CASCADE,
        related_name="members",
    )

    genome = models.ForeignKey(
        Genome,
        on_delete=models.CASCADE,
        related_name="gene_cluster_memberships",
    )

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="gene_cluster_memberships",
        null=True,
        blank=True,
        help_text=(
            "Null if Panaroo referenced a protein ID that could not "
            "be matched back to an imported Protein row."
        ),
    )

    class Meta:
        unique_together = ("gene_cluster", "genome", "protein")

    def __str__(self):
        return f"{self.gene_cluster.cluster_name} - {self.genome}"
    