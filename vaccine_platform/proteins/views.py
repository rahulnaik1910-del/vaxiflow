from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator

from users.models import Analysis
from .models import Protein


def protein_list(request, analysis_id):
    """
    Display proteins with search, sorting and pagination.
    """

    analysis = get_object_or_404(
        Analysis,
        id=analysis_id,
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "protein_id",
    )

    proteins = Protein.objects.filter(
        analysis=analysis,
    )

    if search:

        proteins = proteins.filter(
            Q(protein_id__icontains=search)
            | Q(product__icontains=search)
            | Q(gene__icontains=search)
        )

    allowed_sort = {
        "protein_id": "protein_id",
        "length": "length",
        "-length": "-length",
    }

    proteins = proteins.order_by(
        allowed_sort.get(
            sort,
            "protein_id",
        )
    )

    paginator = Paginator(
        proteins,
        50,
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    return render(
        request,
        "proteins/list.html",
        {
            "analysis": analysis,
            "proteins": page_obj,
            "page_obj": page_obj,
            "search": search,
            "sort": sort,
            "total_proteins": paginator.count,
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
