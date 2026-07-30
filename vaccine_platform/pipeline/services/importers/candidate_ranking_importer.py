from django.conf import settings

from pipeline.models import CandidateRankingResult
from pipeline.services.tools.candidate_scorer import (
    CompositeScorer,
)


class CandidateRankingImporter:

    @staticmethod
    def score_and_rank(
        workflow_run,
        proteins,
        deg_screened=True,
        allergenicity_screened=True,
    ):
        """
        workflow_run:  pipeline.models.WorkflowRun
        proteins:      list of Protein instances to score (the
                       final surviving candidates from every prior
                       stage).
        deg_screened:  bool - False if the DEG essential-gene
                       filter stage was skipped for this run (no
                       database configured).
        allergenicity_screened: bool - False if the Allergenicity
                       stage was skipped for this run (no allergen
                       database configured).

        When either flag is False, every created
        CandidateRankingResult is flagged accordingly and its
        explanation is prefixed with a clear disclosure, so nobody
        downstream (admin, report, exports) can mistake an
        unscreened candidate for a validated one.

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

            explanation = result["explanation"]

            disclosures = []

            if not deg_screened:

                disclosures.append(
                    "*** DEG essential-gene screening was SKIPPED "
                    "for this run (no database configured) - this "
                    "candidate's essentiality was NOT confirmed, "
                    "only passed through unscreened. Do not treat "
                    "as a validated essential gene until DEG "
                    "screening is re-run with a real database. ***"
                )

            if not allergenicity_screened:

                disclosures.append(
                    "*** Allergenicity screening was SKIPPED for "
                    "this run (no allergen database configured) - "
                    "this candidate has NOT been confirmed non-"
                    "allergenic, only passed through unscreened. "
                    "***"
                )

            if disclosures:

                explanation = (
                    "\n".join(disclosures) + "\n\n" + explanation
                )

            ranking_objects.append(
                CandidateRankingResult(
                    workflow_run=workflow_run,
                    protein=protein,
                    scorer_name=settings.RANKING_SCORER,
                    deg_screened=deg_screened,
                    allergenicity_screened=(
                        allergenicity_screened
                    ),
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
                    explanation=explanation,
                )
            )

        created = CandidateRankingResult.objects.bulk_create(
            ranking_objects
        )

        log_lines = [
            f"Scored and ranked {len(created)} candidates using "
            f"the '{settings.RANKING_SCORER}' scorer.",
        ]

        if not deg_screened:

            log_lines.append(
                "DEG screening was skipped for this run - all "
                "ranked candidates are flagged deg_screened=False."
            )

        if not allergenicity_screened:

            log_lines.append(
                "Allergenicity screening was skipped for this run "
                "- all ranked candidates are flagged "
                "allergenicity_screened=False."
            )

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
