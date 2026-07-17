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

    latest_analysis = analyses.first()

    protein_count = 0
    signalp_count = 0

    if latest_analysis:

        protein_count = Protein.objects.filter(
            analysis=latest_analysis,
        ).count()

        signalp_count = SignalPResult.objects.filter(
            protein__analysis=latest_analysis,
        ).count()

    context = {

        "project": project,

        "analyses": analyses,

        "latest_analysis": latest_analysis,

        "protein_count": protein_count,

        "signalp_count": signalp_count,

    }

    return render(
        request,
        "analysis/dashboard.html",
        context,
    )
