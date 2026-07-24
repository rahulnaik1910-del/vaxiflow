from django.conf import settings

from pipeline.models import MhcIEpitopeResult


class MhcIEpitopeImporter:

    @staticmethod
    def import_from_rows(protein, rows, method):
        """
        protein: Protein instance.
        rows:    list of dicts from
                 IedbApiClient.query_mhci_binding() - each with
                 "allele", "start", "end", "peptide", "ic50",
                 "percentile_rank" (column set can vary slightly by
                 method, so missing fields are handled gracefully).
        method:  str - the method used, stored for reference.

        Replaces any existing MhcIEpitopeResult rows for this
        protein (idempotent on re-run) and bulk-creates the new set.

        Returns the number of rows created.
        """

        MhcIEpitopeResult.objects.filter(
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

            if row.get("percentile_rank"):
                try:
                    percentile_rank = float(
                        row["percentile_rank"]
                    )
                except ValueError:
                    pass

            is_strong_binder = (
                percentile_rank is not None
                and percentile_rank
                <= settings.IEDB_MHCI_PERCENTILE_THRESHOLD
            )

            result_objects.append(
                MhcIEpitopeResult(
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

        created = MhcIEpitopeResult.objects.bulk_create(
            result_objects
        )

        return len(created)
