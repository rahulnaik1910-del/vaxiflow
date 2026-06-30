from django.db import models

from proteins.models import Protein


class SignalPResult(models.Model):
    """
    Stores SignalP prediction results for a protein.
    """

    protein = models.OneToOneField(
        Protein,
        on_delete=models.CASCADE,
        related_name="signalp_result",
    )

    prediction = models.CharField(
        max_length=50,
    )

    probability = models.FloatField()

    cleavage_site = models.CharField(
        max_length=100,
        blank=True,
    )

    version = models.CharField(
        max_length=50,
        default="SignalP",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):

        return (
            f"{self.protein.protein_id} - "
            f"{self.prediction}"
        )
    