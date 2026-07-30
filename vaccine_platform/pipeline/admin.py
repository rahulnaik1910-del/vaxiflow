from django.contrib import admin

from .models import (
    Workflow,
    WorkflowStage,
    WorkflowRun,
    WorkflowTask,
    PanarooRun,
    GeneCluster,
    GeneClusterMember,
    DegHit,
    PsortbResult,
    PhobiusResult,
    AntigenicityResult,
    AllergenicityResult,
    ToxicityResult,
    BCellEpitopeResult,
    MhcIEpitopeResult,
    MhcIIEpitopeResult,
    CandidateRankingResult,
)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "version",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "is_active",
    )


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):

    list_display = (
        "workflow",
        "order",
        "name",
        "tool_name",
        "enabled",
    )

    ordering = (
        "workflow",
        "order",
    )

    list_filter = (
        "workflow",
        "enabled",
    )

    search_fields = (
        "name",
        "tool_name",
    )


@admin.register(WorkflowRun)
class WorkflowRunAdmin(admin.ModelAdmin):

    list_display = (
        "project",
        "workflow",
        "status",
        "progress",
        "current_stage",
        "started_at",
    )

    search_fields = (
        "project__project_name",
    )

    list_filter = (
        "status",
        "workflow",
    )

    readonly_fields = (
        "started_at",
    )


@admin.register(WorkflowTask)
class WorkflowTaskAdmin(admin.ModelAdmin):

    list_display = (
        "workflow_run",
        "stage",
        "status",
        "started_at",
        "completed_at",
    )

    list_filter = (
        "status",
        "stage",
    )

    search_fields = (
        "workflow_run__project__project_name",
        "stage__name",
    )

    readonly_fields = (
        "started_at",
        "completed_at",
    )

    ordering = (
        "workflow_run",
        "stage__order",
    )


@admin.register(PanarooRun)
class PanarooRunAdmin(admin.ModelAdmin):

    list_display = (
        "workflow_run",
        "status",
        "genome_count",
        "core_gene_count",
        "accessory_gene_count",
        "started_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "workflow_run__project__project_name",
    )

    readonly_fields = (
        "started_at",
        "completed_at",
    )


@admin.register(GeneCluster)
class GeneClusterAdmin(admin.ModelAdmin):

    list_display = (
        "cluster_name",
        "panaroo_run",
        "is_core",
        "is_essential",
        "genome_count",
    )

    list_filter = (
        "is_core",
        "is_essential",
        "panaroo_run",
    )

    search_fields = (
        "cluster_name",
    )


@admin.register(DegHit)
class DegHitAdmin(admin.ModelAdmin):

    list_display = (
        "gene_cluster",
        "subject_id",
        "identity",
        "coverage",
        "evalue",
    )

    search_fields = (
        "gene_cluster__cluster_name",
        "subject_id",
    )


@admin.register(PsortbResult)
class PsortbResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "localization",
        "score",
        "is_surface_exposed",
    )

    list_filter = (
        "localization",
        "is_surface_exposed",
    )

    search_fields = (
        "protein__protein_id",
    )


@admin.register(PhobiusResult)
class PhobiusResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "prediction_source",
        "tm_helix_count",
        "has_signal_peptide",
        "is_favorable_topology",
    )

    list_filter = (
        "prediction_source",
        "has_signal_peptide",
        "is_favorable_topology",
    )

    search_fields = (
        "protein__protein_id",
    )


@admin.register(GeneClusterMember)
class GeneClusterMemberAdmin(admin.ModelAdmin):

    list_display = (
        "gene_cluster",
        "genome",
        "protein",
    )

    list_filter = (
        "genome",
    )

    search_fields = (
        "gene_cluster__cluster_name",
        "protein__protein_id",
    )
    

@admin.register(AntigenicityResult)
class AntigenicityResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "average_propensity",
        "antigenic_residue_fraction",
        "is_antigenic",
    )

    list_filter = (
        "is_antigenic",
    )

    search_fields = (
        "protein__protein_id",
    )


@admin.register(AllergenicityResult)
class AllergenicityResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "best_subject_id",
        "identity",
        "has_sliding_window_hit",
        "has_exact_match",
        "is_allergen",
    )

    list_filter = (
        "is_allergen",
        "has_sliding_window_hit",
        "has_exact_match",
    )

    search_fields = (
        "protein__protein_id",
        "best_subject_id",
    )


@admin.register(ToxicityResult)
class ToxicityResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "ml_score",
        "is_toxic",
    )

    list_filter = (
        "is_toxic",
    )

    search_fields = (
        "protein__protein_id",
    )


@admin.register(BCellEpitopeResult)
class BCellEpitopeResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "method",
        "epitope_residue_count",
        "total_residues_scored",
        "has_epitope",
    )

    list_filter = (
        "has_epitope",
        "method",
    )

    search_fields = (
        "protein__protein_id",
    )


@admin.register(MhcIEpitopeResult)
class MhcIEpitopeResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "allele",
        "peptide",
        "percentile_rank",
        "is_strong_binder",
    )

    list_filter = (
        "allele",
        "is_strong_binder",
    )

    search_fields = (
        "protein__protein_id",
        "peptide",
    )


@admin.register(MhcIIEpitopeResult)
class MhcIIEpitopeResultAdmin(admin.ModelAdmin):

    list_display = (
        "protein",
        "allele",
        "peptide",
        "percentile_rank",
        "is_strong_binder",
    )

    list_filter = (
        "allele",
        "is_strong_binder",
    )

    search_fields = (
        "protein__protein_id",
        "peptide",
    )


@admin.register(CandidateRankingResult)
class CandidateRankingResultAdmin(admin.ModelAdmin):

    list_display = (
        "rank",
        "protein",
        "workflow_run",
        "final_score",
        "scorer_name",
        "deg_screened",
        "allergenicity_screened",
    )

    list_filter = (
        "scorer_name",
        "deg_screened",
        "allergenicity_screened",
        "workflow_run",
    )

    search_fields = (
        "protein__protein_id",
    )
