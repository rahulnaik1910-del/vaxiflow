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
    