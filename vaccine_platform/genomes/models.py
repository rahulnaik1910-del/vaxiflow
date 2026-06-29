from django.db import models
from users.models import Project


class Genome(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="genomes",
    )

    genome_file = models.FileField(
        upload_to="genomes/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.genome_file.name
    