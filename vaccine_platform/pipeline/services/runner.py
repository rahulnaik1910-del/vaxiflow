from django.utils import timezone

from pipeline.models import (
    WorkflowRun,
    WorkflowTask,
)


class PipelineRunner:

    @staticmethod
    def run(workflow_run):

        workflow_run.status = "running"
        workflow_run.save()

        tasks = workflow_run.tasks.order_by(
            "stage__order"
        )

        total_tasks = tasks.count()
        completed_tasks = 0

        for task in tasks:

            task.status = "running"
            task.started_at = timezone.now()
            task.save()

            # ----------------------------
            # Tool execution placeholder
            # ----------------------------

            task.log += (
                f"Running {task.stage.name}\n"
            )

            # Here Bakta, Panaroo,
            # Phobius etc. will run.

            # ----------------------------

            task.status = "completed"
            task.completed_at = timezone.now()
            task.exit_code = 0
            task.save()

            completed_tasks += 1

            workflow_run.current_stage = task.stage

            workflow_run.progress = int(
                (completed_tasks / total_tasks) * 100
            )

            workflow_run.save()

        workflow_run.status = "completed"
        workflow_run.completed_at = timezone.now()
        workflow_run.progress = 100
        workflow_run.save()
        