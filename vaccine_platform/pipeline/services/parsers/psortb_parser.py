from pathlib import Path


class PsortbParser:
    """
    Parses PSORTb terse output.

    Confirmed real format (psort -o terse), tab-separated:

        SeqID	Localization	Score
        test_protein_1 	Unknown	2.00
        test_protein_2 	Cytoplasmic	9.26

    Note PSORTb pads SeqID with a trailing space before the tab -
    this parser strips whitespace from every field.
    """

    def __init__(self, tsv_file):
        self.tsv_file = Path(tsv_file)

    def parse(self):
        """
        Returns a dict keyed by protein_id:
            {
                "test_protein_1": {
                    "localization": "Unknown",
                    "score": 2.0,
                },
                ...
            }
        """

        results = {}

        if not self.tsv_file.exists():
            return results

        with open(self.tsv_file, "r") as handle:

            for raw_line in handle:

                line = raw_line.strip()

                if not line:
                    continue

                if line.startswith("SeqID"):
                    # Header row.
                    continue

                columns = line.split("\t")

                if len(columns) < 3:
                    continue

                protein_id = columns[0].strip()
                localization = columns[1].strip()

                try:
                    score = float(columns[2].strip())
                except ValueError:
                    continue

                results[protein_id] = {
                    "localization": localization,
                    "score": score,
                }

        return results
