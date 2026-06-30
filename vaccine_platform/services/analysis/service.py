from django.utils import timezone

from services.prokka.runner import ProkkaRunner
from services.protein.importer import ProteinImporter


class AnalysisService:
    """
    Executes analysis workflows.
    """

    @staticmethod
    def run_annotation(analysis):

        analysis.status = "running"
        analysis.save()

        runner = ProkkaRunner(analysis)

        result = runner.run()

        analysis.output_directory = result["output_directory"]

        analysis.exit_code = result["return_code"]

        analysis.log = (
            "STDOUT\n"
            "-------------------------\n"
            f"{result['stdout']}\n\n"
            "STDERR\n"
            "-------------------------\n"
            f"{result['stderr']}"
        )

        analysis.completed_at = timezone.now()

        if result["success"]:

            analysis.status = "completed"

            importer = ProteinImporter(analysis)

            protein_count = importer.import_proteins()

            analysis.log += (
                f"\n\nImported Proteins: {protein_count}"
            )

        else:

            analysis.status = "failed"

        analysis.save()

        return analysis
    