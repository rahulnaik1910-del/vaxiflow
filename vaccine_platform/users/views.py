from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Genome


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

    return render(
        request,
        "projects/detail.html",
        {
            "project": project
        }
    )


def upload_genome(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    return render(
        request,
        "genomes/upload.html",
        {
            "project": project
        }
    )
