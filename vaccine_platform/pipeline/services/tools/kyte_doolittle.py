# Kyte & Doolittle (1982), "A simple method for displaying the
# hydropathic character of a protein", J Mol Biol 157(1):105-32.
# Values are the standard published hydropathy index per residue.
KYTE_DOOLITTLE_SCALE = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
    "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
    "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}

# A window of 19 residues is the classic choice for detecting
# alpha-helical transmembrane spans with the Kyte-Doolittle scale
# (long enough to span a membrane-crossing helix, ~20 residues).
WINDOW_SIZE = 19

# A window average above this is considered a strong hydrophobic
# stretch consistent with a transmembrane helix (Kyte & Doolittle's
# own suggested cutoff for membrane-spanning regions).
TM_HYDROPATHY_THRESHOLD = 1.6

# Minimum gap (in residues) between the end of one TM helix window
# and the start of the next, to avoid double-counting a single wide
# hydrophobic stretch as two separate helices.
MIN_HELIX_SEPARATION = 5

# Signal peptides are short (typically 15-30 residues), N-terminal,
# hydrophobic stretches preceded by a slightly positive n-region -
# this heuristic only checks the first SIGNAL_PEPTIDE_SEARCH_REGION
# residues for a qualifying hydrophobic core.
SIGNAL_PEPTIDE_SEARCH_REGION = 30
SIGNAL_PEPTIDE_MIN_HYDROPATHY = 1.5
SIGNAL_PEPTIDE_MIN_CORE_LENGTH = 7


class KyteDoolittleTopologyPredictor:
    """
    A native, dependency-free fallback for transmembrane helix and
    signal peptide prediction, used when the real Phobius binary
    isn't available.

    This is a simplified sliding-window hydropathy method, not a
    trained HMM like Phobius - it will be less accurate, particularly
    for borderline cases and signal-peptide cleavage sites. It exists
    so the pipeline always produces a topology call, and prefers real
    Phobius output automatically whenever the binary is configured.
    """

    @staticmethod
    def _hydropathy_windows(sequence):
        """
        Returns a list of (start_index, average_hydropathy) for
        every window of WINDOW_SIZE residues in the sequence.
        """

        windows = []

        for start in range(0, len(sequence) - WINDOW_SIZE + 1):

            window = sequence[start:start + WINDOW_SIZE]

            scores = [
                KYTE_DOOLITTLE_SCALE.get(residue, 0.0)
                for residue in window
            ]

            average = sum(scores) / len(scores)

            windows.append((start, average))

        return windows

    @staticmethod
    def predict(sequence):
        """
        sequence: str - amino acid sequence (upper case expected).

        Returns a dict matching the shape of a parsed Phobius result:
            {
                "tm_helix_count": <int>,
                "has_signal_peptide": <bool>,
                "topology": <str>,  # human-readable summary, not a
                                    # real Phobius topology string
            }
        """

        sequence = sequence.upper()

        windows = (
            KyteDoolittleTopologyPredictor._hydropathy_windows(
                sequence
            )
        )

        # Collapse consecutive/overlapping windows above threshold
        # into distinct helix regions.
        helix_regions = []
        current_region = None

        for start, average in windows:

            if average >= TM_HYDROPATHY_THRESHOLD:

                if (
                    current_region is not None
                    and start
                    - current_region[1]
                    <= MIN_HELIX_SEPARATION
                ):
                    current_region = (
                        current_region[0],
                        start + WINDOW_SIZE,
                    )
                else:

                    if current_region is not None:
                        helix_regions.append(current_region)

                    current_region = (
                        start,
                        start + WINDOW_SIZE,
                    )

        if current_region is not None:
            helix_regions.append(current_region)

        tm_helix_count = len(helix_regions)

        # Signal peptide heuristic: is there a strong hydrophobic
        # core within the first SIGNAL_PEPTIDE_SEARCH_REGION
        # residues, at least SIGNAL_PEPTIDE_MIN_CORE_LENGTH long?
        n_terminal_region = sequence[
            :SIGNAL_PEPTIDE_SEARCH_REGION
        ]

        has_signal_peptide = False

        if len(n_terminal_region) >= SIGNAL_PEPTIDE_MIN_CORE_LENGTH:

            for start in range(
                0,
                len(n_terminal_region)
                - SIGNAL_PEPTIDE_MIN_CORE_LENGTH
                + 1,
            ):

                core = n_terminal_region[
                    start:start
                    + SIGNAL_PEPTIDE_MIN_CORE_LENGTH
                ]

                scores = [
                    KYTE_DOOLITTLE_SCALE.get(residue, 0.0)
                    for residue in core
                ]

                average = sum(scores) / len(scores)

                if average >= SIGNAL_PEPTIDE_MIN_HYDROPATHY:
                    has_signal_peptide = True
                    break

        topology_summary = (
            f"{tm_helix_count} predicted TM helix region(s)"
            + (
                " with an N-terminal signal peptide"
                if has_signal_peptide
                else ""
            )
            + " (Kyte-Doolittle native fallback, not Phobius)"
        )

        return {
            "tm_helix_count": tm_helix_count,
            "has_signal_peptide": has_signal_peptide,
            "topology": topology_summary,
        }
