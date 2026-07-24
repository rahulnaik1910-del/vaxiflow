import csv
from pathlib import Path


class ToxinPred2Parser:
    """
    Parses ToxinPred2's CSV output.

    Confirmed real format (ran the actual tool to verify this):

        ID,Sequence,ML_Score,Prediction
        protein_1,MASRTV...,0.545,Non-Toxin
        protein_2,GIGAVL...,0.65,Toxin
    """

    def __init__(self, csv_file):
        self.csv_file = Path(csv_file)

    def parse(self):
        """
        Returns a dict keyed by protein_id:
            {
                "protein_1": {
                    "ml_score": 0.545,
                    "is_toxic": False,
                },
                ...
            }
        """

        results = {}

        if not self.csv_file.exists():
            return results

        with open(self.csv_file, newline="") as handle:

            reader = csv.DictReader(handle)

            for row in reader:

                protein_id = row.get("ID", "").strip()

                if not protein_id:
                    continue

                try:
                    ml_score = float(row.get("ML_Score", ""))
                except ValueError:
                    continue

                prediction = row.get("Prediction", "").strip()

                results[protein_id] = {
                    "ml_score": ml_score,
                    "is_toxic": prediction == "Toxin",
                }

        return results
