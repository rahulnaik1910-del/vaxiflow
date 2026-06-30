from django.db import models
from users.models import Analysis


class Protein(models.Model):
    """
    Stores one protein predicted by Prokka.
    """

    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name="proteins",
    )

    protein_id = models.CharField(
        max_length=200,
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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):

        if self.product:
            return f"{self.protein_id} ({self.product})"

        return self.protein_id
    