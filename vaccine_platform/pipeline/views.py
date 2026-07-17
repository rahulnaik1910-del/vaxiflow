from threading import Thread

from django.contrib import messages
from django.shortcuts import (
    get_object_or_404,
    redirect,
)

from users.models import Project

from pipeline.models import (
    Workflow,
    WorkflowRun,
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

        print("PipelineRunner finished successfully")

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
