from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect

from users.models import Project

from pipeline.models import (
    Workflow,
    WorkflowRun,
)

from pipeline.services.task_manager import (
    TaskManager,
)


def start_workflow(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    workflow = get_object_or_404(
        Workflow,
        is_active=True,
    )

    workflow_run = WorkflowRun.objects.create(
        project=project,
        workflow=workflow,
        status="pending",
        progress=0,
    )

    TaskManager.create_tasks(
        workflow_run
    )

    messages.success(
        request,
        "Workflow started successfully."
    )

    return redirect(
        "project_detail",
        project_id=project.id,
    )
