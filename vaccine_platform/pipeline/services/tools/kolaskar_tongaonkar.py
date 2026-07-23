# Kolaskar, A.S. and Tongaonkar, P.C. (1990), "A semi-empirical
# method for prediction of antigenic determinants on protein
# antigens", FEBS Letters 276(1-2):172-174.
#
# Published antigenic propensity (Ap) scale per residue, as widely
# reproduced in subsequent antigenicity-prediction tools (e.g. the
# IEDB Antigenicity Prediction tool, which credits this same source).
ANTIGENIC_PROPENSITY_SCALE = {
    "A": 1.064, "C": 1.412, "D": 0.866, "E": 0.851, "F": 1.091,
    "G": 0.874, "H": 1.105, "I": 1.152, "K": 0.930, "L": 1.250,
    "M": 0.826, "N": 0.776, "P": 1.064, "Q": 1.015, "R": 0.873,
    "S": 1.012, "T": 0.909, "V": 1.383, "W": 0.893, "Y": 1.161,
}

# Fallback value for any non-standard residue character.
DEFAULT_PROPENSITY = sum(ANTIGENIC_PROPENSITY_SCALE.values()) / len(
    ANTIGENIC_PROPENSITY_SCALE
)

# The original method scores centered heptapeptide (7-residue)
# windows.
WINDOW_SIZE = 7


class AntigenicityScorer:
    """
    A native, dependency-free implementation of the Kolaskar-
    Tongaonkar antigenicity prediction method. Used in place of
    VaxiJen, which has no downloadable binary or public API to
    integrate against - this method is real, published, and fully
    reproducible without any external service.
    """

    @staticmethod
    def score(sequence):
        """
        sequence: str - amino acid sequence.

        Returns a dict of raw scores (no threshold applied here -
        that's the importer's job, using
        settings.ANTIGENICITY_THRESHOLD):
            {
                "average_propensity": <float>,
                "antigenic_residue_fraction": <float>,
            }

        `average_propensity` is the whole-protein average Ap value -
        this is the headline antigenicity score.

        `antigenic_residue_fraction` is the fraction of scored
        heptapeptide windows whose local average is itself >= 1.0
        (the original paper's own per-window cutoff, which is
        distinct from - and always applied regardless of -
        settings.ANTIGENICITY_THRESHOLD, since it's an internal
        detail of how the method locates determinant regions) - a
        finer-grained measure of how much of the protein looks like
        an antigenic determinant.
        """

        sequence = sequence.upper()

        residue_scores = [
            ANTIGENIC_PROPENSITY_SCALE.get(
                residue, DEFAULT_PROPENSITY
            )
            for residue in sequence
        ]

        if not residue_scores:

            return {
                "average_propensity": 0.0,
                "antigenic_residue_fraction": 0.0,
            }

        average_propensity = (
            sum(residue_scores) / len(residue_scores)
        )

        # Score every centered heptapeptide window (the original
        # method excludes the first/last 3 residues, which don't
        # have a full centered window).
        window_averages = []

        half_window = WINDOW_SIZE // 2

        for center in range(
            half_window, len(sequence) - half_window
        ):

            window = residue_scores[
                center - half_window:center + half_window + 1
            ]

            window_averages.append(sum(window) / len(window))

        if window_averages:

            antigenic_windows = [
                value
                for value in window_averages
                if value >= 1.0
            ]

            antigenic_residue_fraction = (
                len(antigenic_windows) / len(window_averages)
            )

        else:
            # Sequence shorter than one full window - fall back to
            # the whole-sequence average as the only signal available.
            antigenic_residue_fraction = (
                1.0 if average_propensity >= 1.0 else 0.0
            )

        return {
            "average_propensity": average_propensity,
            "antigenic_residue_fraction": (
                antigenic_residue_fraction
            ),
        }
