from blast.models import BlastResult


class BlastImporter:
    """
    Imports parsed BLAST results into the database.
    """

    @staticmethod
    def import_results(protein, results):

        BlastResult.objects.filter(
            protein=protein
        ).delete()

        created = []

        for result in results:

            blast_result = BlastResult.objects.create(

                protein=protein,

                subject_id=result["subject_id"],

                subject_title=result["subject_title"],

                identity=result["identity"],

                alignment_length=result["alignment_length"],

                evalue=result["evalue"],

                bit_score=result["bit_score"],

            )

            created.append(blast_result)

        return created
    