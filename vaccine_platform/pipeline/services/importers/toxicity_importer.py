from pipeline.models import ToxicityResult
from pipeline.services.parsers.toxinpred2_parser import (
    ToxinPred2Parser,
)


class ToxicityImporter:

    @staticmethod
    def import_results(proteins, output_file):
        """
        proteins:    list of Protein instances that were screened.
        output_file: str/Path - the toxinpred2_results.csv file
                     written by ToxinPred2Executor

        Returns a dict:
            {
                "screened": <int>,
                "toxic": <int>,
                "non_toxic": <int>,
                "missing": <int>,
                "log": <str>,
            }
        """

        parsed = ToxinPred2Parser(output_file).parse()

        log_lines = [
            f"Parsed {len(parsed)} ToxinPred2 predictions from "
            f"{output_file}.",
        ]

        toxic_count = 0
        non_toxic_count = 0
        missing_count = 0

        for protein in proteins:

            prediction = parsed.get(protein.protein_id)

            if prediction is None:
                missing_count += 1
                continue

            ToxicityResult.objects.update_or_create(
                protein=protein,
                defaults={
                    "ml_score": prediction["ml_score"],
                    "is_toxic": prediction["is_toxic"],
                },
            )

            if prediction["is_toxic"]:
                toxic_count += 1
            else:
                non_toxic_count += 1

        log_lines.append(
            f"Result: {toxic_count} toxic, "
            f"{non_toxic_count} non-toxic, "
            f"{missing_count} had no result."
        )

        return {
            "screened": len(proteins),
            "toxic": toxic_count,
            "non_toxic": non_toxic_count,
            "missing": missing_count,
            "log": "\n".join(log_lines),
        }
