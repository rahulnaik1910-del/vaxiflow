import re
from pathlib import Path


class PhobiusParser:
    """
    Parses Phobius "-short" output format.

    Documented format (whitespace-padded columns, header line
    literally spells SEQENCE_ID - that's Phobius's own typo, not
    ours):

        SEQENCE_ID                     TM SP  PREDICTION
        protein_1                       2  0  i54-76o92-114i
        protein_2                       0  1  n8-19c23/24o

    Columns:
        - SEQENCE_ID: query name (matches protein_id)
        - TM: number of predicted transmembrane helices
        - SP: 0 or 1, whether a signal peptide was predicted
        - PREDICTION: raw topology string

    NOTE: this parser is written from Phobius's documented output
    format and has not been validated against a real Phobius run in
    this environment (see PhobiusExecutor docstring) - it has been
    tested against hand-constructed sample files matching the
    documented format.
    """

    def __init__(self, output_file):
        self.output_file = Path(output_file)

    def parse(self):
        """
        Returns a dict keyed by protein_id:
            {
                "protein_1": {
                    "tm_helix_count": 2,
                    "has_signal_peptide": False,
                    "topology": "i54-76o92-114i",
                },
                ...
            }
        """

        results = {}

        if not self.output_file.exists():
            return results

        with open(self.output_file, "r") as handle:

            for raw_line in handle:

                line = raw_line.strip()

                if not line:
                    continue

                if line.startswith("SEQENCE_ID"):
                    # Header row (Phobius's own spelling).
                    continue

                # Columns are whitespace-separated, but PREDICTION
                # itself never contains whitespace, so a plain split
                # is safe here.
                columns = re.split(r"\s+", line)

                if len(columns) < 4:
                    continue

                protein_id = columns[0]

                try:
                    tm_helix_count = int(columns[1])
                except ValueError:
                    continue

                has_signal_peptide = columns[2] == "1"

                topology = columns[3]

                results[protein_id] = {
                    "tm_helix_count": tm_helix_count,
                    "has_signal_peptide": has_signal_peptide,
                    "topology": topology,
                }

        return results
