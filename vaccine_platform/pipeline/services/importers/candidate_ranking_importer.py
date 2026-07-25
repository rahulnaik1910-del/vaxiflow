from django.conf import settings

from pipeline.models import CandidateRankingResult
from pipeline.services.tools.candidate_scorer import (
    CompositeScorer,
)


class CandidateRankingImporter:

    @staticmethod
    def score_and_rank(workflow_run, proteins):
        """
        workflow_run: pipeline.models.WorkflowRun
        proteins:     list of Protein instances to score (the final
                      surviving candidates from every prior stage).

        Scores every protein with the configured scorer
        (settings.RANKING_SCORER - currently always "composite"),
        then assigns rank 1..N by final_score descending.

        Returns a dict:
            {
                "ranked": <int>,
                "log": <str>,
            }
        """

        # Clear any prior ranking for this workflow_run so re-runs
        # are idempotent.
        CandidateRankingResult.objects.filter(
            workflow_run=workflow_run
        ).delete()

        scored = []

        for protein in proteins:

            result = CompositeScorer.score(protein)

            scored.append((protein, result))

        # Rank by final_score descending.
        scored.sort(
            key=lambda item: item[1]["final_score"],
            reverse=True,
        )

        ranking_objects = []

        for rank, (protein, result) in enumerate(scored, start=1):

            components = result["components"]

            ranking_objects.append(
                CandidateRankingResult(
                    workflow_run=workflow_run,
                    protein=protein,
                    scorer_name=settings.RANKING_SCORER,
                    antigenicity_component=components[
                        "antigenicity"
                    ],
                    localization_component=components[
                        "localization"
                    ],
                    epitope_component=components["epitope"],
                    mhci_coverage_component=components[
                        "mhci_coverage"
                    ],
                    mhcii_coverage_component=components[
                        "mhcii_coverage"
                    ],
                    final_score=result["final_score"],
                    rank=rank,
                    explanation=result["explanation"],
                )
            )

        created = CandidateRankingResult.objects.bulk_create(
            ranking_objects
        )

        log_lines = [
            f"Scored and ranked {len(created)} candidates using "
            f"the '{settings.RANKING_SCORER}' scorer.",
        ]

        if created:

            top = created[0]

            log_lines.append(
                f"Top candidate: {top.protein.protein_id} "
                f"(score {round(top.final_score, 3)})"
            )

        return {
            "ranked": len(created),
            "log": "\n".join(log_lines),
        }
