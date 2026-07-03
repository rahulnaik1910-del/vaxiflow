from django.conf import settings

from proteins.models import Protein

from blast.services.exporter import ProteinExporter
from blast.services.runner import BlastRunner
from blast.services.parser import BlastParser
from blast.services.importer import BlastImporter


class BlastService:
    """
    Complete BLAST workflow.

    Protein
        ↓
    Export FASTA
        ↓
    Run BLASTP
        ↓
    Parse XML
        ↓
    Store Results
    """

    @staticmethod
    def run(protein: Protein):

        working_directory = (
            settings.BLAST_OUTPUT_DIRECTORY
            / protein.protein_id
        )

        fasta_file = ProteinExporter.export(
            protein=protein,
            output_directory=working_directory,
        )

        database = settings.BLAST_DATABASES[
            "human_swissprot"
        ]

        xml_file = BlastRunner.run(
            query_fasta=fasta_file,
            database=database,
            output_directory=working_directory,
        )

        parsed_results = BlastParser.parse(
            xml_file
        )

        imported_results = BlastImporter.import_results(
            protein=protein,
            results=parsed_results,
        )

        return imported_results
    