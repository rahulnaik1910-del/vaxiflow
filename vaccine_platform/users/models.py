from django.db import models


class Project(models.Model):

    project_name = models.CharField(max_length=200)

    organism = models.CharField(max_length=300)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name


class Genome(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="genomes"
    )

    genome_file = models.FileField(
        upload_to="genomes/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.genome_file.name


class Analysis(models.Model):

    ANALYSIS_TYPES = [
        ("annotation", "Genome Annotation"),
        ("signalp", "SignalP"),
        ("tmhmm", "TMHMM"),
        ("psortb", "PSORTb"),
        ("blast", "BLAST"),
        ("vaxijen", "VaxiJen"),
        ("ai", "AI Analysis"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="analyses",
    )

    genome = models.ForeignKey(
        Genome,
        on_delete=models.CASCADE,
        related_name="analyses",
    )

    analysis_type = models.CharField(
        max_length=50,
        choices=ANALYSIS_TYPES,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
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
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.project.project_name} - "
            f"{self.get_analysis_type_display()}"
        )
    