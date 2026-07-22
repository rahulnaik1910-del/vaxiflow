from pathlib import Path

from django.conf import settings
from django.utils import timezone

from pipeline.models import (
    WorkflowTask,
    PanarooRun,
    GeneCluster,
)

from pipeline.services.tools.bakta import (
    BaktaExecutor,
)

from pipeline.services.tools.panaroo import (
    PanarooExecutor,
)

from pipeline.services.tools.deg import (
    DegExecutor,
)

from pipeline.services.importers.bakta_importer import (
    BaktaImporter,
)

from pipeline.services.importers.panaroo_importer import (
    PanarooImporter,
)

from pipeline.services.importers.deg_importer import (
    DegImporter,
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

            elif tool_name == "panaroo":

                success = (
                    PipelineRunner._run_panaroo_stage(
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

            elif tool_name == "deg_filter":

                success = (
                    PipelineRunner._run_deg_filter_stage(
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
    def _run_panaroo_stage(
        workflow_run,
        task,
    ):
        """
        Run Panaroo across every genome in the project that has a
        completed Bakta annotation.

        Panaroo computes a pan-genome by comparing genomes to each
        other, so it requires at least
        settings.PANAROO_MIN_GENOMES (default 2) successfully
        Bakta-annotated genomes to run at all.
        """

        task.status = "running"
        task.started_at = timezone.now()
        task.completed_at = None
        task.exit_code = None
        task.log = (
            "Starting Panaroo pan-genome analysis stage.\n"
        )
        task.save()

        bakta_analyses = (
            Analysis.objects.filter(
                project=workflow_run.project,
                analysis_type="bakta",
                status="completed",
            )
            .select_related("genome")
            .order_by("genome_id", "completed_at")
        )

        # Keep only the latest completed Bakta analysis per genome,
        # in case a genome was re-annotated more than once.
        latest_by_genome = {}

        for analysis in bakta_analyses:
            latest_by_genome[analysis.genome_id] = analysis

        genome_count = len(latest_by_genome)

        min_genomes = settings.PANAROO_MIN_GENOMES

        task.log += (
            f"Genomes with a completed Bakta annotation: "
            f"{genome_count} (minimum required: {min_genomes})\n"
        )
        task.save()

        if genome_count < min_genomes:

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = 1
            task.log += (
                f"\nPanaroo requires at least {min_genomes} "
                "successfully Bakta-annotated genomes to compute "
                "a pan-genome, but only "
                f"{genome_count} were available. Upload and "
                "annotate additional genomes for this project, "
                "then re-run the workflow.\n"
            )
            task.save()

            return False

        gff3_paths = []

        for genome_id, analysis in latest_by_genome.items():

            gff3_path = (
                Path(analysis.output_directory)
                / f"genome_{genome_id}_annotation.gff3"
            )
            gff3_paths.append(gff3_path)

        panaroo_run = PanarooRun.objects.create(
            workflow_run=workflow_run,
            status="running",
            genome_count=genome_count,
            started_at=timezone.now(),
        )

        output_dir = (
            Path(settings.MEDIA_ROOT)
            / "pipeline_runs"
            / f"run_{workflow_run.id}"
            / "panaroo"
        )

        task.log += (
            f"\nRunning Panaroo on {genome_count} genomes...\n"
        )
        task.save()

        result = PanarooExecutor.run(
            gff3_paths=gff3_paths,
            output_dir=output_dir,
            panaroo_run=panaroo_run,
        )

        task.log += (
            "\n"
            f"{result['log']}\n"
        )
        task.save()

        panaroo_run.output_directory = result["output_directory"]
        panaroo_run.exit_code = result["exit_code"]

        if result["exit_code"] != 0:

            panaroo_run.status = "failed"
            panaroo_run.log = result["log"]
            panaroo_run.completed_at = timezone.now()
            panaroo_run.save()

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = result["exit_code"]
            task.log += (
                "\nPanaroo pan-genome analysis failed.\n"
            )
            task.save()

            return False

        import_result = PanarooImporter.import_from_output(
            panaroo_run=panaroo_run,
            output_dir=result["output_directory"],
            total_genomes=genome_count,
        )

        task.log += (
            "\n"
            f"{import_result['log']}\n"
        )
        task.save()

        panaroo_run.core_gene_count = import_result["core_count"]
        panaroo_run.accessory_gene_count = (
            import_result["accessory_count"]
        )
        panaroo_run.status = "completed"
        panaroo_run.log = (
            f"{result['log']}\n\n{import_result['log']}"
        )
        panaroo_run.completed_at = timezone.now()
        panaroo_run.save()

        task.status = "completed"
        task.completed_at = timezone.now()
        task.exit_code = 0
        task.log += (
            "\nPanaroo pan-genome analysis stage "
            "completed successfully.\n"
        )
        task.save()

        return True

    @staticmethod
    def _run_deg_filter_stage(
        workflow_run,
        task,
    ):
        """
        Screen the project's core genome (GeneCluster rows with
        is_core=True from the most recent PanarooRun) against the
        Database of Essential Genes (DEG) using BLASTP, and flag
        each core cluster as essential or not.

        One representative protein per cluster is used as the query
        (the first member, by id) rather than blasting every member
        protein - this is standard practice, since members of the
        same orthologous cluster are expected to be near-identical.
        """

        task.status = "running"
        task.started_at = timezone.now()
        task.completed_at = None
        task.exit_code = None
        task.log = (
            "Starting Essential Gene Filter (DEG) stage.\n"
        )
        task.save()

        panaroo_run = (
            PanarooRun.objects.filter(
                workflow_run=workflow_run,
                status="completed",
            )
            .order_by("-completed_at")
            .first()
        )

        if panaroo_run is None:

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = 1
            task.log += (
                "\nNo completed Panaroo run was found for this "
                "workflow. The DEG filter requires a core genome "
                "from Panaroo to screen.\n"
            )
            task.save()

            return False

        core_clusters = (
            GeneCluster.objects.filter(
                panaroo_run=panaroo_run,
                is_core=True,
            )
            .prefetch_related("members__protein")
        )

        representative_proteins = {}

        for cluster in core_clusters:

            member = (
                cluster.members
                .filter(protein__isnull=False)
                .order_by("protein_id")
                .first()
            )

            if member is not None:
                representative_proteins[cluster.id] = (
                    cluster,
                    member.protein,
                )

        task.log += (
            f"Core gene clusters found: {core_clusters.count()}\n"
            "Core clusters with a resolvable representative "
            f"protein: {len(representative_proteins)}\n"
        )
        task.save()

        if not representative_proteins:

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = 1
            task.log += (
                "\nNo core cluster had a representative protein to "
                "screen. Nothing to do.\n"
            )
            task.save()

            return False

        output_dir = (
            Path(settings.MEDIA_ROOT)
            / "pipeline_runs"
            / f"run_{workflow_run.id}"
            / "deg"
        )

        query_fasta = DegExecutor.write_query_fasta(
            representative_proteins=[
                (cluster_id, protein)
                for cluster_id, (
                    _,
                    protein,
                ) in representative_proteins.items()
            ],
            output_dir=output_dir,
        )

        task.log += (
            f"\nWrote {len(representative_proteins)} representative "
            f"sequences to {query_fasta}\n"
            "Running BLASTP against the DEG database...\n"
        )
        task.save()

        result = DegExecutor.run(
            query_fasta=query_fasta,
            output_dir=output_dir,
        )

        task.log += (
            "\n"
            f"{result['log']}\n"
        )
        task.save()

        if result["exit_code"] != 0:

            task.status = "failed"
            task.completed_at = timezone.now()
            task.exit_code = result["exit_code"]
            task.log += (
                "\nDEG screening (BLASTP) failed.\n"
            )
            task.save()

            return False

        import_result = DegImporter.import_results(
            representative_proteins=representative_proteins,
            output_file=result["output_file"],
        )

        task.log += (
            "\n"
            f"{import_result['log']}\n"
        )
        task.save()

        task.status = "completed"
        task.completed_at = timezone.now()
        task.exit_code = 0
        task.log += (
            "\nEssential Gene Filter (DEG) stage completed "
            "successfully.\n"
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
        