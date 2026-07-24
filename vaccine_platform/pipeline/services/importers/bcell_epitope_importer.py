from pipeline.models import BCellEpitopeResult


class BCellEpitopeImporter:

    @staticmethod
    def import_from_rows(protein, rows, method):
        """
        protein: Protein instance.
        rows:    list of dicts from
                 IedbApiClient.query_bcell_epitope() - each with
                 "Position", "Residue", "Score", "Assignment".
        method:  str - the method used, stored for reference.

        Returns the created/updated BCellEpitopeResult.
        """

        epitope_residue_count = sum(
            1
            for row in rows
            if row.get("Assignment", "").strip() == "E"
        )

        total_residues_scored = len(rows)

        epitope_fraction = (
            epitope_residue_count / total_residues_scored
            if total_residues_scored > 0
            else 0.0
        )

        raw_result = "\n".join(
            "\t".join(row.values()) for row in rows
        )

        result, _ = BCellEpitopeResult.objects.update_or_create(
            protein=protein,
            defaults={
                "method": method,
                "total_residues_scored": total_residues_scored,
                "epitope_residue_count": epitope_residue_count,
                "epitope_fraction": epitope_fraction,
                "has_epitope": epitope_residue_count > 0,
                "raw_result": raw_result,
            },
        )

        return result
