from django.db import models


class Project(models.Model):

    GRAM_STAIN_CHOICES = [
        ("negative", "Gram Negative"),
        ("positive", "Gram Positive"),
        ("archaea", "Archaea"),
    ]

    project_name = models.CharField(max_length=200)

    organism = models.CharField(max_length=300)

    gram_stain = models.CharField(
        max_length=20,
        choices=GRAM_STAIN_CHOICES,
        default="negative",
        help_text=(
            "Determines which PSORTb analysis mode is used for "
            "subcellular localization prediction. Defaults to "
            "Gram Negative - check this is correct for your "
            "organism before running the PSORTb stage."
        ),
    )

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
        ("bakta", "Bakta Annotation"),
        ("panaroo", "Panaroo Pan-Genome"),
        ("deg_filter", "Essential Gene Filter (DEG)"),
        ("human_homology", "Human Homology (DIAMOND/BLAST)"),
        ("psortb", "PSORTb Localization"),
        ("phobius", "Phobius"),
        ("antigenicity", "Antigenicity"),
        ("allergenicity", "Allergenicity"),
        ("toxicity", "Toxicity"),
        ("iedb", "IEDB Epitope Prediction"),
        ("ai_ranking", "AI Candidate Ranking"),
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
    