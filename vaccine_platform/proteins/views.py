from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from users.models import Analysis
from .models import Protein


def protein_list(request, analysis_id):
    """
    Display proteins with search support.
    """

    analysis = get_object_or_404(
        Analysis,
        id=analysis_id,
    )

    search = request.GET.get("search", "").strip()

    proteins = Protein.objects.filter(
        analysis=analysis,
    )

    if search:

        proteins = proteins.filter(
            Q(protein_id__icontains=search) |
            Q(product__icontains=search) |
            Q(gene__icontains=search)
        )

    proteins = proteins.order_by("protein_id")

    return render(
        request,
        "proteins/list.html",
        {
            "analysis": analysis,
            "proteins": proteins,
            "search": search,
        },
    )


def protein_detail(request, protein_id):
    """
    Display one protein.
    """

    protein = get_object_or_404(
        Protein,
        id=protein_id,
    )

    return render(
        request,
        "proteins/detail.html",
        {
            "protein": protein,
        },
    )
