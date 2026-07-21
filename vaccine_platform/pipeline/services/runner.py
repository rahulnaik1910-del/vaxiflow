from django.utils import timezone

from pipeline.models import (
    WorkflowTask,
)

from pipeline.services.tools.bakta import (
    BaktaExecutor,
)

from pipeline.services.importers.bakta_importer import (
    BaktaImporter,
)

from users.models import Analysis

from users.validators import (
    validate_nucleotide_fasta,
)


class PipelineRunner:
    """
    Executes the stages of a VaxiFlow workflow.

    Current implementation:
        - Stage 1 / Bakta:
            Runs real Bakta Light annotation.
        - Other stages:
            Marked as skipped until their
            executors are implemented.
    """

    @staticmethod
    def run(workflow_run):

        workflow_run.status = "running"
        workflow_run.started_at = (
            workflow_run.started_at
            or timezone.now()
        )
        workflow_run.completed_at = None
        workflow_run.progress = 0
        workflow_run.save()

        tasks = (
            workflow_run.tasks
            .select_related("stage")
            .order_by("stage__order")
        )

        total_tasks = tasks.count()

        if total_tasks == 0:

            workflow_run.status = "failed"
            workflow_run.completed_at = timezone.now()
            workflow_run.progress = 0
            workflow_run.save()

            return

        for task in tasks:

            tool_name = (
                task.stage.tool_name
                .strip()
                .lower()
            )

            workflow_run.current_stage = task.stage
            workflow_run.save()

            if tool_name == "bakta":

                success = (
                    PipelineRunner._run_bakta_stage(
                        workflow_run,
                        task,
                    )
                )

                if not success:

                    workflow_run.status = "failed"
                    workflow_run.completed_at = (
                        timezone.now()
                    )
                    workflow_run.save()

                    return

            else:

                PipelineRunner._skip_stage(
                    task
                )

            processed_tasks = (
                workflow_run.tasks.filter(
                    status__in=[
                        "completed",
                        "skipped",
                    ]
                ).count()
            )

            workflow_run.progress = int(
                (
                    processed_tasks
                    / total_tasks
                )
                * 100
            )

            workflow_run.save()

        workflow_run.status = "completed"
        workflow_run.completed_at = timezone.now()
        workflow_run.progress = 100
        workflow_run.save()

    @staticmethod
    def _run_bakta_stage(
        workflow_run,
        task,
    ):
        """
        Run Bakta on every valid nucleotide genome
        uploaded to the project.

        Legacy protein FASTA files are ignored.
        """

        task.status = "running"
        task.started_at = timezone.now()
        task.completed_at = None
        task.exit_code = None
        task.log = (
            "Starting Bakta Light annotation stage.\n"
        )
        task.save()

        genomes = (
            workflow_run.project.genomes.all()
            .order_by("uploaded_at")
        )

        if not genomes.exists():

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = 1
            task.log += (
                "No uploaded genome files were found "
                "for this project.\n"
            )
            task.save()

            return False

        valid_genomes = []
        skipped_genomes = []

        for genome in genomes:

            is_valid, validation_message = (
                validate_nucleotide_fasta(
                    genome.genome_file.path
                )
            )

            if is_valid:

                valid_genomes.append(
                    genome
                )

            else:

                skipped_genomes.append(
                    (
                        genome,
                        validation_message,
                    )
                )

        if skipped_genomes:

            task.log += (
                "\nLegacy or invalid files skipped:\n"
            )

            for genome, reason in skipped_genomes:

                task.log += (
                    f"- Genome ID {genome.id}: "
                    f"{genome.genome_file.name}\n"
                    f"  Reason: {reason}\n"
                )

        if not valid_genomes:

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = 1
            task.log += (
                "\nNo valid nucleotide genome FASTA "
                "files were available for Bakta.\n"
            )
            task.save()

            return False

        task.log += (
            "\nValid nucleotide genomes selected "
            f"for Bakta: {len(valid_genomes)}\n"
        )
        task.save()

        for genome in valid_genomes:

            task.log += (
                "\n"
                "====================================\n"
                f"Running Bakta for Genome ID "
                f"{genome.id}\n"
                f"File: "
                f"{genome.genome_file.name}\n"
                "====================================\n"
            )
            task.save()

            analysis = Analysis.objects.create(
                project=workflow_run.project,
                genome=genome,
                analysis_type="bakta",
                status="running",
            )

            result = BaktaExecutor.run(
                genome=genome,
                workflow_run=workflow_run,
            )

            task.log += (
                "\n"
                f"{result['log']}\n"
            )
            task.save()

            analysis.output_directory = (
                result["output_directory"]
            )
            analysis.exit_code = result["exit_code"]

            if result["exit_code"] != 0:

                analysis.status = "failed"
                analysis.log = result["log"]
                analysis.completed_at = timezone.now()
                analysis.save()

                task.status = "failed"
                task.completed_at = timezone.now()
                task.exit_code = (
                    result["exit_code"]
                )
                task.log += (
                    "\nBakta annotation failed.\n"
                )
                task.save()

                return False

            import_result = BaktaImporter.import_from_output(
                genome=genome,
                analysis=analysis,
                output_dir=result["output_directory"],
                prefix=result["prefix"],
            )

            task.log += (
                "\n"
                f"{import_result['log']}\n"
            )
            task.save()

            analysis.status = "completed"
            analysis.log = (
                f"{result['log']}\n\n{import_result['log']}"
            )
            analysis.completed_at = timezone.now()
            analysis.save()

        task.status = "completed"
        task.completed_at = timezone.now()
        task.exit_code = 0
        task.log += (
            "\nBakta Light annotation stage "
            "completed successfully.\n"
        )
        task.save()

        return True

    @staticmethod
    def _skip_stage(task):
        """
        Skip stages whose real executors have
        not yet been implemented.
        """

        task.status = "skipped"
        task.started_at = timezone.now()
        task.completed_at = timezone.now()
        task.exit_code = 0
        task.log = (
            f"{task.stage.name} skipped.\n"
            f"Tool '{task.stage.tool_name}' "
            "has not been integrated yet."
        )
        task.save()
        