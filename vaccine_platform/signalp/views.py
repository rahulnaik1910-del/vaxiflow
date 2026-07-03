from pathlib import Path

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from users.models import Analysis

from signalp.models import SignalPResult
from signalp.services.service import SignalPService


def run_signalp(request, analysis_id):
    """
    Execute SignalP for one annotation analysis.
    """

    analysis = get_object_or_404(
        Analysis,
        id=analysis_id,
    )

    #
    # Placeholder paths.
    #
    # These will become dynamic once
    # SignalP is installed.
    #

    fasta_file = Path(
        analysis.output_directory
    ) / "proteins.faa"

    output_directory = Path(
        analysis.output_directory
    ) / "signalp"

    try:

        service = SignalPService(
            fasta_file=fasta_file,
            output_directory=output_directory,
        )

        service.execute()

    except Exception as error:

        return render(
            request,
            "signalp/error.html",
            {
                "analysis": analysis,
                "error": str(error),
            },
        )

    return redirect(
        "signalp_results",
        analysis_id=analysis.id,
    )


def signalp_results(request, analysis_id):
    """
    Display SignalP predictions.
    """

    analysis = get_object_or_404(
        Analysis,
        id=analysis_id,
    )

    results = SignalPResult.objects.filter(
        protein__analysis=analysis,
    ).order_by(
        "protein__protein_id"
    )

    return render(
        request,
        "signalp/results.html",
        {
            "analysis": analysis,
            "results": results,
        },
    )
