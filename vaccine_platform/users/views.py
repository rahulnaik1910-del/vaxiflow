from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse

from .models import Project, Genome, Analysis


ALLOWED_EXTENSIONS = [
    ".fna",
    ".fasta",
    ".fa",
    ".faa",
    ".gff",
    ".gbk",
    ".gbff",
]


def home(request):

    projects = Project.objects.all().order_by("-created_at")

    return render(
        request,
        "dashboard/home.html",
        {
            "projects": projects
        }
    )


def create_project(request):

    if request.method == "POST":

        Project.objects.create(
            project_name=request.POST.get("project_name"),
            organism=request.POST.get("organism"),
            description=request.POST.get("description"),
        )

        return redirect("/")

    return render(
        request,
        "projects/create.html"
    )


def project_detail(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    genomes = Genome.objects.filter(
        project=project
    ).order_by("-uploaded_at")

    analyses = Analysis.objects.filter(
        project=project
    ).order_by("-started_at")

    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "genomes": genomes,
            "analyses": analyses,
        }
    )


def upload_genome(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    error = None

    if request.method == "POST":

        uploaded_file = request.FILES.get("genome_file")

        if uploaded_file:

            extension = Path(uploaded_file.name).suffix.lower()

            if extension not in ALLOWED_EXTENSIONS:

                error = (
                    "Only FASTA, FNA, FA, FAA, "
                    "GFF, GBK and GBFF files are allowed."
                )

            else:

                Genome.objects.create(
                    project=project,
                    genome_file=uploaded_file,
                )

                return redirect(
                    "project_detail",
                    project_id=project.id
                )

    return render(
        request,
        "genomes/upload.html",
        {
            "project": project,
            "error": error,
        }
    )


def download_genome(request, genome_id):

    genome = get_object_or_404(
        Genome,
        id=genome_id
    )

    return FileResponse(
        genome.genome_file.open("rb"),
        as_attachment=True,
        filename=Path(genome.genome_file.name).name,
    )


def run_annotation(request, genome_id):

    genome = get_object_or_404(
        Genome,
        id=genome_id
    )

    Analysis.objects.create(
        project=genome.project,
        genome=genome,
        analysis_type="annotation",
        status="pending",
    )

    return redirect(
        "project_detail",
        project_id=genome.project.id,
    )
