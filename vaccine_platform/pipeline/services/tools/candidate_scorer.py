from django.conf import settings


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


class CompositeScorer:
    """
    A transparent, explainable composite scoring function for final
    vaccine candidate ranking - NOT a trained ML model. There is no
    labeled dataset of experimentally validated vaccine candidates
    to train a real classifier/regressor against, so this combines
    the real quantitative signals already computed by every prior
    pipeline stage into a single weighted score instead of
    pretending to be "AI".

    ARCHITECTURAL SEAM FOR A FUTURE REAL ML MODEL: this class's
    `score()` method is the only integration point PipelineRunner
    calls (selected via settings.RANKING_SCORER, currently always
    "composite"). A future MLScorer class implementing the same
    score(protein, ...) -> dict contract could be swapped in via
    that setting without changing any other part of the pipeline.
    """

    @staticmethod
    def _normalize_antigenicity(antigenicity_result):

        if antigenicity_result is None:
            return 0.0

        low = settings.RANKING_ANTIGENICITY_MIN
        high = settings.RANKING_ANTIGENICITY_MAX

        value = antigenicity_result.average_propensity

        return _clamp((value - low) / (high - low))

    @staticmethod
    def _normalize_localization(psortb_result):

        if psortb_result is None:
            return 0.0

        # PSORTb's own score scale is 0-10.
        return _clamp(psortb_result.score / 10.0)

    @staticmethod
    def _normalize_epitope(bcell_result):

        if bcell_result is None:
            return 0.0

        return _clamp(bcell_result.epitope_fraction)

    @staticmethod
    def _mhc_coverage(mhc_results_queryset):
        """
        Fraction of distinct alleles tested that produced at least
        one strong binder - a simple proxy for population coverage
        breadth.
        """

        alleles_tested = set(
            mhc_results_queryset.values_list(
                "allele", flat=True
            )
        )

        if not alleles_tested:
            return 0.0

        alleles_with_strong_binder = set(
            mhc_results_queryset.filter(
                is_strong_binder=True
            ).values_list("allele", flat=True)
        )

        return len(alleles_with_strong_binder) / len(
            alleles_tested
        )

    @staticmethod
    def score(protein):
        """
        protein: Protein instance - expected to already have related
                 AntigenicityResult, PsortbResult, BCellEpitopeResult,
                 and mhci/mhcii_epitope_results.

        Returns a dict:
            {
                "final_score": <float>,
                "components": {
                    "antigenicity": <float 0-1>,
                    "localization": <float 0-1>,
                    "epitope": <float 0-1>,
                    "mhci_coverage": <float 0-1>,
                    "mhcii_coverage": <float 0-1>,
                },
                "explanation": <str>,
            }
        """

        antigenicity_result = (
            protein.antigenicity_results.order_by(
                "-created_at"
            ).first()
        )

        psortb_result = (
            protein.psortb_results.order_by(
                "-created_at"
            ).first()
        )

        bcell_result = getattr(
            protein, "bcell_epitope_result", None
        )

        antigenicity = (
            CompositeScorer._normalize_antigenicity(
                antigenicity_result
            )
        )

        localization = (
            CompositeScorer._normalize_localization(
                psortb_result
            )
        )

        epitope = CompositeScorer._normalize_epitope(
            bcell_result
        )

        mhci_coverage = CompositeScorer._mhc_coverage(
            protein.mhci_epitope_results.all()
        )

        mhcii_coverage = CompositeScorer._mhc_coverage(
            protein.mhcii_epitope_results.all()
        )

        components = {
            "antigenicity": antigenicity,
            "localization": localization,
            "epitope": epitope,
            "mhci_coverage": mhci_coverage,
            "mhcii_coverage": mhcii_coverage,
        }

        weights = settings.RANKING_COMPONENT_WEIGHTS

        final_score = sum(
            components[name] * weight
            for name, weight in weights.items()
            if name in components
        )

        explanation_lines = [
            f"Antigenicity: {antigenicity:.2f} "
            f"(weight {weights.get('antigenicity', 0):.2f})",
            f"Surface localization confidence: {localization:.2f} "
            f"(weight {weights.get('localization', 0):.2f})",
            f"B-cell epitope density: {epitope:.2f} "
            f"(weight {weights.get('epitope', 0):.2f})",
            f"MHC-I allele coverage: {mhci_coverage:.2f} "
            f"(weight {weights.get('mhci_coverage', 0):.2f})",
            f"MHC-II allele coverage: {mhcii_coverage:.2f} "
            f"(weight {weights.get('mhcii_coverage', 0):.2f})",
            f"Final weighted score: {final_score:.3f}",
        ]

        return {
            "final_score": final_score,
            "components": components,
            "explanation": "\n".join(explanation_lines),
        }
