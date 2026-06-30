from pathlib import Path

from proteins.models import Protein
from services.protein.parser import ProteinParser


class ProteinImporter:
    """
    Imports proteins from a Prokka .faa file
    into the Protein database.
    """

    def __init__(self, analysis):

        self.analysis = analysis

    def import_proteins(self):

        faa_file = (
            Path(self.analysis.output_directory)
            / "annotation.faa"
        )

        parser = ProteinParser(faa_file)

        proteins = parser.parse()

        # Remove old proteins if this analysis
        # is imported again.
        Protein.objects.filter(
            analysis=self.analysis
        ).delete()

        created = 0

        for protein in proteins:

            Protein.objects.create(

                analysis=self.analysis,

                protein_id=protein["protein_id"],

                gene="",

                product=protein["product"],

                sequence=protein["sequence"],

                length=protein["length"],

            )

            created += 1

        return created
    