from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.contrib import messages

from proteins.models import Protein
from blast.models import BlastResult
from blast.services.service import BlastService


def run_blast(request, protein_id):
    """
    Execute BLAST for one protein.
    """

    protein = get_object_or_404(
        Protein,
        id=protein_id,
    )

    try:

        BlastService.run(protein)

        messages.success(
            request,
            "BLAST completed successfully.",
        )

    except Exception as error:

        messages.error(
            request,
            f"BLAST failed: {error}",
        )

    return redirect(
        "blast_results",
        protein.id,
    )


def blast_results(request, protein_id):
    """
    Display BLAST results.
    """

    protein = get_object_or_404(
        Protein,
        id=protein_id,
    )

    results = BlastResult.objects.filter(
        protein=protein
    ).order_by(
        "evalue"
    )

    return render(
        request,
        "blast/results.html",
        {
            "protein": protein,
            "results": results,
        },
    )
