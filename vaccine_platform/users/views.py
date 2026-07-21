from pathlib import Path

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.http import FileResponse
from django.contrib import messages

from .models import (
    Project,
    Genome,
    Analysis,
)
from .validators import (
    ALLOWED_GENOME_EXTENSIONS,
    validate_nucleotide_fasta,
)

from proteins.models import Protein
from pipeline.models import WorkflowRun


def home(request):
    """
    VaxiFlow Dashboard
    """

    projects = Project.objects.all().order_by(
        "-created_at"
    )

    total_projects = Project.objects.count()
    total_genomes = Genome.objects.count()
    total_analyses = Analysis.objects.count()
    total_proteins = Protein.objects.count()

    recent_projects = (
        Project.objects.all()
        .order_by("-created_at")[:5]
    )

    pipeline = [
        {
            "name": "Genome Upload",
            "status": "completed",
        },
        {
            "name": "Genome Annotation",
            "status": "completed",
        },
        {
            "name": "Protein Import",
            "status": "completed",
        },
        {
            "name": "SignalP",
            "status": "waiting",
        },
        {
            "name": "TMHMM",
            "status": "waiting",
        },
        {
            "name": "PSORTb",
            "status": "waiting",
        },
        {
            "name": "BLAST",
            "status": "waiting",
        },
        {
            "name": "VaxiJen",
            "status": "waiting",
        },
        {
            "name": "AI Ranking",
            "status": "waiting",
        },
    ]

    return render(
        request,
        "dashboard/home.html",
        {
            "projects": projects,
            "recent_projects": recent_projects,
            "total_projects": total_projects,
            "total_genomes": total_genomes,
            "total_analyses": total_analyses,
            "total_proteins": total_proteins,
            "pipeline": pipeline,
        },
    )


def create_project(request):

    if request.method == "POST":

        Project.objects.create(
            project_name=request.POST.get(
                "project_name"
            ),
            organism=request.POST.get(
                "organism"
            ),
            description=request.POST.get(
                "description"
            ),
        )

        return redirect("/")

    return render(
        request,
        "projects/create.html",
    )


def project_detail(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    genomes = (
        Genome.objects.filter(
            project=project,
        )
        .order_by("-uploaded_at")
    )

    analyses = (
        Analysis.objects.filter(
            project=project,
        )
        .order_by("-started_at")
    )

    workflow_run = (
        WorkflowRun.objects.filter(
            project=project,
        )
        .order_by("-started_at")
        .first()
    )

    workflow_tasks = []

    if workflow_run:

        workflow_tasks = (
            workflow_run.tasks.select_related(
                "stage"
            )
            .order_by(
                "stage__order"
            )
        )

    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "genomes": genomes,
            "analyses": analyses,
            "workflow_run": workflow_run,
            "workflow_tasks": workflow_tasks,
        },
    )


def upload_genome(request, project_id):
    """
    Upload and validate a nucleotide genome FASTA file.

    Only .fasta, .fa, and .fna files containing
    nucleotide sequences are accepted.
    """

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    error = None

    if request.method == "POST":

        uploaded_file = request.FILES.get(
            "genome_file"
        )

        if not uploaded_file:

            error = (
                "Please select a genome file."
            )

        else:

            extension = Path(
                uploaded_file.name
            ).suffix.lower()

            if (
                extension
                not in ALLOWED_GENOME_EXTENSIONS
            ):

                error = (
                    "Only nucleotide genome FASTA "
                    "files (.fasta, .fa, .fna) "
                    "are allowed."
                )

            else:

                genome = Genome.objects.create(
                    project=project,
                    genome_file=uploaded_file,
                )

                is_valid, validation_message = (
                    validate_nucleotide_fasta(
                        genome.genome_file.path
                    )
                )

                if not is_valid:

                    # Delete the invalid physical
                    # file from storage.
                    genome.genome_file.delete(
                        save=False
                    )

                    # Delete the invalid database
                    # record.
                    genome.delete()

                    error = validation_message

                else:

                    messages.success(
                        request,
                        "Genome uploaded and "
                        "validated successfully.",
                    )

                    return redirect(
                        "project_detail",
                        project_id=project.id,
                    )

    return render(
        request,
        "genomes/upload.html",
        {
            "project": project,
            "error": error,
        },
    )


def download_genome(request, genome_id):

    genome = get_object_or_404(
        Genome,
        id=genome_id,
    )

    return FileResponse(
        genome.genome_file.open("rb"),
        as_attachment=True,
        filename=Path(
            genome.genome_file.name
        ).name,
    )



# NOTE: The old per-genome `run_annotation` view has been removed.
# It called a legacy Prokka-based AnalysisService that is no longer
# part of this codebase. Genome annotation now runs exclusively
# through the Bakta pipeline via `start_workflow` (see pipeline app),
# which is triggered from the project detail page.
