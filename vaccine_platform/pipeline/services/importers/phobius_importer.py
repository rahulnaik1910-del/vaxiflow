from django.conf import settings

from pipeline.models import PhobiusResult
from pipeline.services.parsers.phobius_parser import PhobiusParser


class PhobiusImporter:

    @staticmethod
    def import_from_predictions(
        proteins,
        predictions,
        prediction_source,
    ):
        """
        proteins:           list of Protein instances that were
                             screened.
        predictions:         dict keyed by protein_id:
                             {
                                 "tm_helix_count": <int>,
                                 "has_signal_peptide": <bool>,
                                 "topology": <str>,
                             }
        prediction_source:  one of
                            PhobiusResult.PREDICTION_SOURCE_CHOICES

        Returns a dict:
            {
                "screened": <int>,
                "favorable_topology": <int>,
                "unfavorable_topology": <int>,
                "missing": <int>,
                "log": <str>,
            }
        """

        log_lines = [
            f"Prediction source: {prediction_source}",
            "Max transmembrane helices allowed for a favorable "
            f"vaccine candidate: {settings.PHOBIUS_MAX_TM_HELICES}",
        ]

        favorable_count = 0
        unfavorable_count = 0
        missing_count = 0

        for protein in proteins:

            prediction = predictions.get(protein.protein_id)

            if prediction is None:
                missing_count += 1
                continue

            is_favorable = (
                prediction["tm_helix_count"]
                <= settings.PHOBIUS_MAX_TM_HELICES
            )

            PhobiusResult.objects.update_or_create(
                protein=protein,
                defaults={
                    "prediction_source": prediction_source,
                    "tm_helix_count": (
                        prediction["tm_helix_count"]
                    ),
                    "has_signal_peptide": (
                        prediction["has_signal_peptide"]
                    ),
                    "topology": prediction["topology"],
                    "is_favorable_topology": is_favorable,
                },
            )

            if is_favorable:
                favorable_count += 1
            else:
                unfavorable_count += 1

        log_lines.append(
            f"Result: {favorable_count} favorable topology, "
            f"{unfavorable_count} unfavorable (too many TM "
            f"helices), {missing_count} had no result."
        )

        return {
            "screened": len(proteins),
            "favorable_topology": favorable_count,
            "unfavorable_topology": unfavorable_count,
            "missing": missing_count,
            "log": "\n".join(log_lines),
        }

    @staticmethod
    def import_results(proteins, output_file):
        """
        Back-compat wrapper: parses real Phobius output from a file
        and imports it as prediction_source="phobius".
        """

        predictions = PhobiusParser(output_file).parse()

        return PhobiusImporter.import_from_predictions(
            proteins=proteins,
            predictions=predictions,
            prediction_source="phobius",
        )
