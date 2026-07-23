from django.conf import settings

from pipeline.models import PhobiusResult
from pipeline.services.parsers.phobius_parser import PhobiusParser


class PhobiusImporter:

    @staticmethod
    def import_results(proteins, output_file):
        """
        proteins:    list of Protein instances that were screened.
        output_file: str/Path - the phobius_short.txt file written
                     by PhobiusExecutor

        Returns a dict:
            {
                "screened": <int>,
                "favorable_topology": <int>,
                "unfavorable_topology": <int>,
                "missing": <int>,
                "log": <str>,
            }
        """

        parsed = PhobiusParser(output_file).parse()

        log_lines = [
            f"Parsed {len(parsed)} topology predictions from "
            f"{output_file}.",
            "Max transmembrane helices allowed for a favorable "
            f"vaccine candidate: {settings.PHOBIUS_MAX_TM_HELICES}",
        ]

        favorable_count = 0
        unfavorable_count = 0
        missing_count = 0

        for protein in proteins:

            prediction = parsed.get(protein.protein_id)

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
            f"helices), {missing_count} had no Phobius result."
        )

        return {
            "screened": len(proteins),
            "favorable_topology": favorable_count,
            "unfavorable_topology": unfavorable_count,
            "missing": missing_count,
            "log": "\n".join(log_lines),
        }
