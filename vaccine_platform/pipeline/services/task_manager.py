from pipeline.models import WorkflowTask


class TaskManager:
    """
    Creates WorkflowTask records
    from all enabled WorkflowStages.
    """

    @staticmethod
    def create_tasks(workflow_run):

        workflow = workflow_run.workflow

        stages = workflow.stages.filter(
            enabled=True
        ).order_by(
            "order"
        )

        created_tasks = []

        for stage in stages:

            task = WorkflowTask.objects.create(
                workflow_run=workflow_run,
                stage=stage,
                status="pending",
            )

            created_tasks.append(task)

        return created_tasks
    