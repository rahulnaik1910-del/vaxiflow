from django.utils import timezone

from services.prokka.runner import ProkkaRunner
from services.protein.importer import ProteinImporter


class AnalysisService:

    @staticmethod
    def run_annotation(analysis):

        try:

            print("STEP 1")

            analysis.status = "running"

            print("STEP 1A")

            analysis.save()

            print("STEP 1B")

            runner = ProkkaRunner(analysis)

            print("STEP 2")

            result = runner.run()

            print("STEP 3")

            analysis.output_directory = result["output_directory"]
            analysis.exit_code = result["return_code"]

            analysis.log = (
                f"STDOUT\n{result['stdout']}\n\n"
                f"STDERR\n{result['stderr']}"
            )

            analysis.completed_at = timezone.now()

            if result["success"]:

                print("STEP 4")

                analysis.status = "completed"

                importer = ProteinImporter(analysis)

                protein_count = importer.import_proteins()

                print(f"Imported {protein_count}")

            else:

                print("STEP 5")

                analysis.status = "failed"

            analysis.save()

            print("STEP 6")

            return analysis

        except Exception as e:

            print("EXCEPTION OCCURRED")
            print(type(e))
            print(e)

            raise
        