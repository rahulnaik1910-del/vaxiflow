from django.utils import timezone

from services.prokka.runner import ProkkaRunner


class AnalysisService:
    """
    Executes analysis workflows and updates
    analysis status, logs and output location.
    """

    @staticmethod
    def run_annotation(analysis):

        # -----------------------------
        # Mark analysis as running
        # -----------------------------
        analysis.status = "running"
        analysis.save()

        runner = ProkkaRunner(analysis)

        result = runner.run()

        # -----------------------------
        # Save execution information
        # -----------------------------
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

        else:

            analysis.status = "failed"

        analysis.save()

        return analysis
    