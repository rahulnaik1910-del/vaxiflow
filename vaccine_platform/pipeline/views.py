from threading import Thread

from django.contrib import messages
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from users.models import Project

from pipeline.models import (
    Workflow,
    WorkflowRun,
    CandidateRankingResult,
)

from pipeline.services.task_manager import TaskManager
from pipeline.services.runner import PipelineRunner


def _run_pipeline(workflow_run_id):
    print("=" * 60)
    print("BACKGROUND THREAD STARTED")
    print(f"WorkflowRun ID: {workflow_run_id}")

    try:
        workflow_run = WorkflowRun.objects.get(id=workflow_run_id)

        print("Calling PipelineRunner.run()")

        PipelineRunner.run(workflow_run)

        workflow_run.refresh_from_db()

        if workflow_run.status == "completed":
            print(
                "PipelineRunner finished - workflow_run status: "
                "completed"
            )
        else:
            print(
                "PipelineRunner finished - workflow_run status: "
                f"{workflow_run.status} (NOT a success - check "
                "WorkflowTask logs for the failing stage)"
            )

    except Exception as e:
        print("PIPELINE ERROR")
        print(repr(e))

        try:
            workflow_run = WorkflowRun.objects.get(id=workflow_run_id)
            workflow_run.status = "failed"
            workflow_run.save(update_fields=["status"])
        except Exception:
            pass

    print("=" * 60)


def start_workflow(request, project_id):

    print("=" * 60)
    print(">>> START_WORKFLOW CALLED <<<")

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    print(f"1. Project loaded: {project.project_name}")

    running_workflow = WorkflowRun.objects.filter(
        project=project,
        status__in=["pending", "running"],
    ).exists()

    print(f"2. Running workflow exists: {running_workflow}")

    if running_workflow:
        print("3. Duplicate workflow blocked")

        messages.warning(
            request,
            "A workflow is already running for this project."
        )

        return redirect(
            "project_detail",
            project_id=project.id,
        )

    print("4. Looking for active workflow...")

    workflow = get_object_or_404(
        Workflow,
        is_active=True,
    )

    print(f"5. Active workflow found: {workflow.name}")

    workflow_run = WorkflowRun.objects.create(
        project=project,
        workflow=workflow,
        status="pending",
        progress=0,
    )

    print(f"6. Created WorkflowRun #{workflow_run.id}")

    TaskManager.create_tasks(workflow_run)

    print("7. Workflow tasks created")

    thread = Thread(
        target=_run_pipeline,
        args=(workflow_run.id,),
        daemon=True,
    )

    thread.start()

    print("8. Background thread launched")

    messages.success(
        request,
        "Workflow started successfully."
    )

    print("=" * 60)

    return redirect(
        "project_detail",
        project_id=project.id,
    )

def candidate_report(request, project_id):
    """
    Interactive Report: the final ranked vaccine candidate list for
    a project's most recent completed workflow run.
    """

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    workflow_run = (
        WorkflowRun.objects.filter(
            project=project,
            candidate_rankings__isnull=False,
        )
        .order_by("-completed_at")
        .distinct()
        .first()
    )

    rankings = []

    if workflow_run:

        rankings = (
            CandidateRankingResult.objects.filter(
                workflow_run=workflow_run,
            )
            .select_related(
                "protein",
            )
            .order_by("rank")
        )

    context = {

        "project": project,

        "workflow_run": workflow_run,

        "rankings": rankings,

    }

    return render(
        request,
        "pipeline/report.html",
        context,
    )


def candidate_detail(request, ranking_id):
    """
    Full stage-by-stage breakdown for a single ranked candidate.
    """

    ranking = get_object_or_404(
        CandidateRankingResult,
        id=ranking_id,
    )

    protein = ranking.protein

    antigenicity = (
        protein.antigenicity_results
        .order_by("-created_at")
        .first()
    )

    psortb = (
        protein.psortb_results
        .order_by("-created_at")
        .first()
    )

    phobius = (
        protein.phobius_results
        .order_by("-created_at")
        .first()
    )

    allergenicity = (
        protein.allergenicity_results
        .order_by("-created_at")
        .first()
    )

    toxicity = (
        protein.toxicity_results
        .order_by("-created_at")
        .first()
    )

    bcell = getattr(protein, "bcell_epitope_result", None)

    mhci_binders = (
        protein.mhci_epitope_results.filter(
            is_strong_binder=True,
        ).order_by("percentile_rank")
    )

    mhcii_binders = (
        protein.mhcii_epitope_results.filter(
            is_strong_binder=True,
        ).order_by("percentile_rank")
    )

    context = {

        "ranking": ranking,

        "protein": protein,

        "antigenicity": antigenicity,

        "psortb": psortb,

        "phobius": phobius,

        "allergenicity": allergenicity,

        "toxicity": toxicity,

        "bcell": bcell,

        "mhci_binders": mhci_binders,

        "mhcii_binders": mhcii_binders,

    }

    return render(
        request,
        "pipeline/candidate_detail.html",
        context,
    )
