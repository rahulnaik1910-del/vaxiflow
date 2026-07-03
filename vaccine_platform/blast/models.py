from django.db import models

from proteins.models import Protein


class BlastResult(models.Model):
    """
    Stores BLASTP results for a protein.
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="blast_results",
    )

    subject_id = models.CharField(
        max_length=255,
    )

    subject_title = models.TextField()

    identity = models.FloatField()

    alignment_length = models.IntegerField()

    evalue = models.FloatField()

    bit_score = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> "
            f"{self.subject_id}"
        )
    