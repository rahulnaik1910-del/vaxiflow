from django.conf import settings

from pipeline.models import AntigenicityResult
from pipeline.services.tools.kolaskar_tongaonkar import (
    AntigenicityScorer,
)


class AntigenicityImporter:

    @staticmethod
    def score_and_import(proteins):
        """
        proteins: list of Protein instances to score.

        Computes the Kolaskar-Tongaonkar score for each protein
        directly (no external file to parse - this is a pure
        calculation) and creates/updates an AntigenicityResult row.

        Returns a dict:
            {
                "screened": <int>,
                "antigenic": <int>,
                "not_antigenic": <int>,
                "log": <str>,
            }
        """

        log_lines = [
            f"Scoring {len(proteins)} proteins with the "
            "Kolaskar-Tongaonkar method.",
            "Antigenicity threshold (average propensity): "
            f"{settings.ANTIGENICITY_THRESHOLD}",
        ]

        antigenic_count = 0
        not_antigenic_count = 0

        for protein in proteins:

            scores = AntigenicityScorer.score(protein.sequence)

            is_antigenic = (
                scores["average_propensity"]
                >= settings.ANTIGENICITY_THRESHOLD
            )

            AntigenicityResult.objects.update_or_create(
                protein=protein,
                defaults={
                    "average_propensity": (
                        scores["average_propensity"]
                    ),
                    "antigenic_residue_fraction": (
                        scores["antigenic_residue_fraction"]
                    ),
                    "is_antigenic": is_antigenic,
                },
            )

            if is_antigenic:
                antigenic_count += 1
            else:
                not_antigenic_count += 1

        log_lines.append(
            f"Result: {antigenic_count} antigenic, "
            f"{not_antigenic_count} not antigenic."
        )

        return {
            "screened": len(proteins),
            "antigenic": antigenic_count,
            "not_antigenic": not_antigenic_count,
            "log": "\n".join(log_lines),
        }
