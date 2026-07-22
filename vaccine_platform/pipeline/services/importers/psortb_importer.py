from django.conf import settings

from pipeline.models import PsortbResult
from pipeline.services.parsers.psortb_parser import PsortbParser


class PsortbImporter:

    @staticmethod
    def import_results(proteins, output_file):
        """
        proteins:    list of Protein instances that were screened
                     (used to detect proteins PSORTb didn't return a
                     result for, e.g. if a run partially failed).
        output_file: str/Path - the psortb_terse.tsv file written by
                     PsortbExecutor

        Returns a dict:
            {
                "screened": <int>,
                "surface_exposed": <int>,
                "not_surface_exposed": <int>,
                "missing": <int>,
                "log": <str>,
            }
        """

        parsed = PsortbParser(output_file).parse()

        log_lines = [
            f"Parsed {len(parsed)} localization predictions from "
            f"{output_file}.",
            "Surface-exposed localizations considered vaccine "
            f"targets: {settings.PSORTB_SURFACE_LOCALIZATIONS}",
        ]

        surface_count = 0
        not_surface_count = 0
        missing_count = 0

        for protein in proteins:

            prediction = parsed.get(protein.protein_id)

            if prediction is None:
                missing_count += 1
                continue

            is_surface_exposed = (
                prediction["localization"]
                in settings.PSORTB_SURFACE_LOCALIZATIONS
            )

            PsortbResult.objects.update_or_create(
                protein=protein,
                defaults={
                    "localization": prediction["localization"],
                    "score": prediction["score"],
                    "is_surface_exposed": is_surface_exposed,
                },
            )

            if is_surface_exposed:
                surface_count += 1
            else:
                not_surface_count += 1

        log_lines.append(
            f"Result: {surface_count} surface-exposed, "
            f"{not_surface_count} not surface-exposed, "
            f"{missing_count} had no PSORTb result at all."
        )

        return {
            "screened": len(proteins),
            "surface_exposed": surface_count,
            "not_surface_exposed": not_surface_count,
            "missing": missing_count,
            "log": "\n".join(log_lines),
        }
