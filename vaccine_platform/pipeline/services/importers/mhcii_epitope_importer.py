from django.conf import settings

from pipeline.models import MhcIIEpitopeResult


class MhcIIEpitopeImporter:

    @staticmethod
    def import_from_rows(protein, rows, method):
        """
        Mirrors MhcIEpitopeImporter.import_from_rows, for MHC-II
        binding results.
        """

        MhcIIEpitopeResult.objects.filter(
            protein=protein
        ).delete()

        result_objects = []

        for row in rows:

            try:
                start = int(row.get("start", 0))
                end = int(row.get("end", 0))
            except ValueError:
                continue

            peptide = row.get("peptide", "").strip()

            if not peptide:
                continue

            ic50 = None
            percentile_rank = None

            if row.get("ic50"):
                try:
                    ic50 = float(row["ic50"])
                except ValueError:
                    pass

            if row.get("percentile_rank") or row.get(
                "adjusted_rank"
            ):
                try:
                    percentile_rank = float(
                        row.get("percentile_rank")
                        or row.get("adjusted_rank")
                    )
                except (ValueError, TypeError):
                    pass

            is_strong_binder = (
                percentile_rank is not None
                and percentile_rank
                <= settings.IEDB_MHCII_PERCENTILE_THRESHOLD
            )

            result_objects.append(
                MhcIIEpitopeResult(
                    protein=protein,
                    allele=row.get("allele", "").strip(),
                    peptide=peptide,
                    start=start,
                    end=end,
                    method=method,
                    ic50=ic50,
                    percentile_rank=percentile_rank,
                    is_strong_binder=is_strong_binder,
                )
            )

        created = MhcIIEpitopeResult.objects.bulk_create(
            result_objects
        )

        return len(created)
