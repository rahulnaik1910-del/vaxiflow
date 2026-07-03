from django.shortcuts import (
    render,
    get_object_or_404,
)

from users.models import (
    Project,
    Analysis,
)

from proteins.models import Protein
from signalp.models import SignalPResult


def analysis_dashboard(request, project_id):
    """
    Main Analysis Center dashboard.
    """

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    analyses = Analysis.objects.filter(
        project=project,
    ).order_by(
        "-started_at"
    )

    protein_count = Protein.objects.filter(
        analysis__project=project,
    ).count()

    signalp_count = SignalPResult.objects.filter(
        protein__analysis__project=project,
    ).count()

    context = {

        "project": project,

        "analyses": analyses,

        "protein_count": protein_count,

        "signalp_count": signalp_count,

    }

    return render(
        request,
        "analysis/dashboard.html",
        context,
    )
