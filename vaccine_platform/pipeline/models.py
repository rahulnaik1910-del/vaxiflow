from django.db import models
from users.models import Project, Genome
from proteins.models import Protein


class Workflow(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkflowStage(models.Model):

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="stages",
    )

    order = models.PositiveIntegerField()

    name = models.CharField(max_length=200)

    tool_name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("workflow", "order")

    def __str__(self):
        return f"{self.order}. {self.name}"


class WorkflowRun(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="workflow_runs",
    )

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="runs",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    progress = models.PositiveIntegerField(default=0)

    current_stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.project.project_name} - Run #{self.pk}"


class WorkflowTask(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    workflow_run = models.ForeignKey(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    log = models.TextField(
        blank=True,
    )

    exit_code = models.IntegerField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["stage__order"]
        unique_together = ("workflow_run", "stage")

    def __str__(self):
        return (
            f"{self.workflow_run.project.project_name} - "
            f"{self.stage.name}"
        )


class PanarooRun(models.Model):
    """
    One Panaroo pan-genome analysis for a single WorkflowRun.

    Unlike Bakta (which produces one Analysis per genome), Panaroo
    operates across every genome in the project at once, so this is
    a single record per WorkflowRun, not per genome.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    workflow_run = models.OneToOneField(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name="panaroo_run",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    genome_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of genomes included in this Panaroo run.",
    )

    core_gene_count = models.PositiveIntegerField(
        default=0,
    )

    accessory_gene_count = models.PositiveIntegerField(
        default=0,
    )

    output_directory = models.CharField(
        max_length=500,
        blank=True,
    )

    log = models.TextField(
        blank=True,
    )

    exit_code = models.IntegerField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.workflow_run.project.project_name} - "
            f"Panaroo Run #{self.pk}"
        )


class GeneCluster(models.Model):
    """
    One orthologous gene cluster identified by Panaroo, i.e. one row
    of gene_presence_absence.csv.
    """

    panaroo_run = models.ForeignKey(
        PanarooRun,
        on_delete=models.CASCADE,
        related_name="gene_clusters",
    )

    cluster_name = models.CharField(
        max_length=300,
        help_text="Panaroo's gene/cluster name, e.g. 'dnaA'.",
    )

    is_core = models.BooleanField(
        default=False,
        help_text=(
            "True if this gene is present in enough genomes to be "
            "considered part of the core genome."
        ),
    )

    is_essential = models.BooleanField(
        default=False,
        help_text=(
            "True if this gene's representative protein had a "
            "significant BLAST hit against the Database of "
            "Essential Genes (DEG), above the configured identity/"
            "e-value/coverage thresholds."
        ),
    )

    genome_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of genomes in which this gene was found.",
    )

    class Meta:
        ordering = ["-is_core", "cluster_name"]

    def __str__(self):
        kind = "core" if self.is_core else "accessory"
        return f"{self.cluster_name} ({kind})"


class GeneClusterMember(models.Model):
    """
    Links a GeneCluster to the specific Protein (from a specific
    genome) that belongs to it.
    """

    gene_cluster = models.ForeignKey(
        GeneCluster,
        on_delete=models.CASCADE,
        related_name="members",
    )

    genome = models.ForeignKey(
        Genome,
        on_delete=models.CASCADE,
        related_name="gene_cluster_memberships",
    )

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="gene_cluster_memberships",
        null=True,
        blank=True,
        help_text=(
            "Null if Panaroo referenced a protein ID that could not "
            "be matched back to an imported Protein row."
        ),
    )

    class Meta:
        unique_together = ("gene_cluster", "genome", "protein")

    def __str__(self):
        return f"{self.gene_cluster.cluster_name} - {self.genome}"


class DegHit(models.Model):
    """
    Stores the best BLASTP hit of a core GeneCluster's representative
    protein against the Database of Essential Genes (DEG).

    One row per GeneCluster that was screened (whether or not it
    produced a hit above threshold - GeneCluster.is_essential records
    the pass/fail decision, this table keeps the raw evidence).
    """

    gene_cluster = models.OneToOneField(
        GeneCluster,
        on_delete=models.CASCADE,
        related_name="deg_hit",
    )

    representative_protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="deg_hits",
        help_text=(
            "Which member protein of the gene cluster was used as "
            "the query sequence."
        ),
    )

    subject_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="DEG entry ID of the best hit, if any.",
    )

    identity = models.FloatField(
        null=True,
        blank=True,
    )

    alignment_length = models.IntegerField(
        null=True,
        blank=True,
    )

    coverage = models.FloatField(
        null=True,
        blank=True,
        help_text="alignment_length / query length, as a percent.",
    )

    evalue = models.FloatField(
        null=True,
        blank=True,
    )

    bit_score = models.FloatField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.gene_cluster.cluster_name} -> "
            f"{self.subject_id or 'no hit'}"
        )


class PsortbResult(models.Model):
    """
    Stores the PSORTb subcellular localization prediction for one
    protein (terse output: SeqID, Localization, Score).
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="psortb_results",
    )

    localization = models.CharField(
        max_length=100,
    )

    score = models.FloatField()

    is_surface_exposed = models.BooleanField(
        default=False,
        help_text=(
            "True if `localization` is one of "
            "settings.PSORTB_SURFACE_LOCALIZATIONS - i.e. this "
            "protein is a plausible vaccine target location."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> {self.localization} "
            f"({self.score})"
        )


class PhobiusResult(models.Model):
    """
    Stores a signal peptide + transmembrane topology prediction for
    one protein (either from real Phobius, or from the native
    Kyte-Doolittle fallback when Phobius isn't installed).
    """

    PREDICTION_SOURCE_CHOICES = [
        ("phobius", "Phobius (real binary)"),
        (
            "kyte_doolittle_fallback",
            "Kyte-Doolittle (native fallback)",
        ),
    ]

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="phobius_results",
    )

    prediction_source = models.CharField(
        max_length=30,
        choices=PREDICTION_SOURCE_CHOICES,
        default="phobius",
        help_text=(
            "Which method produced this result. Real Phobius is "
            "more accurate than the native fallback - check this "
            "field before trusting borderline calls."
        ),
    )

    tm_helix_count = models.PositiveIntegerField(
        default=0,
    )

    has_signal_peptide = models.BooleanField(
        default=False,
    )

    topology = models.CharField(
        max_length=500,
        blank=True,
        help_text="Raw PREDICTION string from Phobius short output.",
    )

    is_favorable_topology = models.BooleanField(
        default=False,
        help_text=(
            "True if tm_helix_count <= "
            "settings.PHOBIUS_MAX_TM_HELICES - i.e. this protein "
            "isn't buried in too many membrane-spanning segments "
            "to be a practical vaccine candidate."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> "
            f"{self.tm_helix_count} TM helices, "
            f"SP={self.has_signal_peptide}"
        )


class AntigenicityResult(models.Model):
    """
    Stores the Kolaskar-Tongaonkar antigenicity prediction for one
    protein. This is computed natively (see
    pipeline.services.tools.kolaskar_tongaonkar.AntigenicityScorer)
    rather than via an external tool, since VaxiJen has no
    downloadable binary or public API to integrate against.
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="antigenicity_results",
    )

    average_propensity = models.FloatField(
        help_text=(
            "Whole-protein average Kolaskar-Tongaonkar antigenic "
            "propensity score."
        ),
    )

    antigenic_residue_fraction = models.FloatField(
        help_text=(
            "Fraction of scored heptapeptide windows above the "
            "method's own per-window cutoff - a finer-grained "
            "measure of how much of the protein looks antigenic."
        ),
    )

    is_antigenic = models.BooleanField(
        default=False,
        help_text=(
            "True if average_propensity >= "
            "settings.ANTIGENICITY_THRESHOLD (default 1.0, the "
            "cutoff from the original Kolaskar-Tongaonkar paper)."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> "
            f"{round(self.average_propensity, 3)} "
            f"({'antigenic' if self.is_antigenic else 'not antigenic'})"
        )


class AllergenicityResult(models.Model):
    """
    Stores the FAO/WHO (2001) homology-based allergenicity screening
    result for one protein: BLASTP against a curated allergen
    database (e.g. AllergenOnline) plus an exact short-peptide
    match check, since AllerTOP has no downloadable binary or API to
    integrate against.
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="allergenicity_results",
    )

    best_subject_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Allergen database entry ID of the best BLAST hit.",
    )

    identity = models.FloatField(
        null=True,
        blank=True,
    )

    alignment_length = models.IntegerField(
        null=True,
        blank=True,
    )

    evalue = models.FloatField(
        null=True,
        blank=True,
    )

    bit_score = models.FloatField(
        null=True,
        blank=True,
    )

    has_sliding_window_hit = models.BooleanField(
        default=False,
        help_text=(
            "True if identity >= settings.ALLERGEN_MIN_IDENTITY "
            "over an alignment >= "
            "settings.ALLERGEN_MIN_ALIGNMENT_LENGTH amino acids "
            "(the FAO/WHO 35%/80aa criterion)."
        ),
    )

    has_exact_match = models.BooleanField(
        default=False,
        help_text=(
            "True if this protein shares a contiguous "
            "settings.ALLERGEN_EXACT_MATCH_LENGTH-mer (default 6) "
            "with any sequence in the allergen database (the "
            "FAO/WHO exact-match criterion)."
        ),
    )

    is_allergen = models.BooleanField(
        default=False,
        help_text=(
            "True if either has_sliding_window_hit or "
            "has_exact_match is True - i.e. this protein is "
            "flagged as a potential allergen and is a poor vaccine "
            "candidate regardless of its other scores."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> "
            f"{'allergen' if self.is_allergen else 'not allergen'}"
        )


class ToxicityResult(models.Model):
    """
    Stores the ToxinPred2 (Raghava lab) toxicity prediction for one
    protein. Unlike VaxiJen/AllerTOP/Phobius, ToxinPred2 is a
    genuinely pip-installable, verified-working tool - no fallback
    needed for this stage.
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="toxicity_results",
    )

    ml_score = models.FloatField(
        help_text="ToxinPred2's raw ML_Score output (0.0-1.0).",
    )

    is_toxic = models.BooleanField(
        default=False,
        help_text=(
            "True if ToxinPred2 predicted 'Toxin' (ml_score >= "
            "settings.TOXINPRED2_THRESHOLD, default 0.6)."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> "
            f"{'toxic' if self.is_toxic else 'non-toxic'} "
            f"({self.ml_score})"
        )


class BCellEpitopeResult(models.Model):
    """
    Stores IEDB B-cell (linear/continuous) epitope prediction for
    one protein - one row per protein, summarizing the per-residue
    Bepipred-2.0 scan.
    """

    protein = models.OneToOneField(
        Protein,
        on_delete=models.CASCADE,
        related_name="bcell_epitope_result",
    )

    method = models.CharField(
        max_length=50,
        default="Bepipred-2.0",
    )

    total_residues_scored = models.PositiveIntegerField(
        default=0,
    )

    epitope_residue_count = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Number of residues Bepipred assigned as part of a "
            "predicted linear epitope ('E' assignment)."
        ),
    )

    epitope_fraction = models.FloatField(
        default=0.0,
    )

    has_epitope = models.BooleanField(
        default=False,
        help_text="True if epitope_residue_count > 0.",
    )

    raw_result = models.TextField(
        blank=True,
        help_text="Raw tab-delimited IEDB API response.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.protein.protein_id} -> "
            f"{self.epitope_residue_count}/"
            f"{self.total_residues_scored} epitope residues"
        )


class MhcIEpitopeResult(models.Model):
    """
    Stores one predicted MHC class I binding peptide (one row per
    peptide/allele combination - a protein typically produces many).
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="mhci_epitope_results",
    )

    allele = models.CharField(
        max_length=50,
    )

    peptide = models.CharField(
        max_length=50,
    )

    start = models.PositiveIntegerField()

    end = models.PositiveIntegerField()

    method = models.CharField(
        max_length=50,
        default="recommended",
    )

    ic50 = models.FloatField(
        null=True,
        blank=True,
    )

    percentile_rank = models.FloatField(
        null=True,
        blank=True,
    )

    is_strong_binder = models.BooleanField(
        default=False,
        help_text=(
            "True if percentile_rank <= "
            "settings.IEDB_MHCI_PERCENTILE_THRESHOLD "
            "(default 2.0, the conventional strong-binder cutoff)."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.protein.protein_id} -> {self.peptide} ({self.allele})"


class MhcIIEpitopeResult(models.Model):
    """
    Stores one predicted MHC class II binding peptide (one row per
    peptide/allele combination).
    """

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="mhcii_epitope_results",
    )

    allele = models.CharField(
        max_length=50,
    )

    peptide = models.CharField(
        max_length=50,
    )

    start = models.PositiveIntegerField()

    end = models.PositiveIntegerField()

    method = models.CharField(
        max_length=50,
        default="recommended",
    )

    ic50 = models.FloatField(
        null=True,
        blank=True,
    )

    percentile_rank = models.FloatField(
        null=True,
        blank=True,
    )

    is_strong_binder = models.BooleanField(
        default=False,
        help_text=(
            "True if percentile_rank <= "
            "settings.IEDB_MHCII_PERCENTILE_THRESHOLD "
            "(default 10.0 - MHC-II binding prediction is less "
            "precise than MHC-I, so this cutoff is more permissive)."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.protein.protein_id} -> {self.peptide} ({self.allele})"
    

class CandidateRankingResult(models.Model):
    """
    Stores the final composite ranking score for one protein within
    one WorkflowRun - the consolidated output of every prior stage,
    used to produce the ranked candidate list for the Interactive
    Report.

    This is a transparent, explainable weighted composite score, NOT
    a trained ML model - there is no labeled dataset of validated
    vaccine candidates to train one honestly. `scorer_name` records
    which scoring method produced a result, so a genuine trained
    model can be introduced later (see settings.RANKING_SCORER and
    pipeline.services.tools.candidate_scorer) without losing the
    ability to tell old and new results apart.
    """

    workflow_run = models.ForeignKey(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name="candidate_rankings",
    )

    protein = models.ForeignKey(
        Protein,
        on_delete=models.CASCADE,
        related_name="candidate_rankings",
    )

    scorer_name = models.CharField(
        max_length=50,
        default="composite",
    )

    deg_screened = models.BooleanField(
        default=True,
        help_text=(
            "False if the DEG essential-gene screening stage was "
            "skipped for this workflow_run (no database "
            "configured) - if so, this candidate's essentiality "
            "was never confirmed, only assumed as a widened, "
            "unscreened pass-through. Always check this before "
            "treating a candidate as a validated essential gene."
        ),
    )

    antigenicity_component = models.FloatField(default=0.0)

    localization_component = models.FloatField(default=0.0)

    epitope_component = models.FloatField(default=0.0)

    mhci_coverage_component = models.FloatField(default=0.0)

    mhcii_coverage_component = models.FloatField(default=0.0)

    final_score = models.FloatField(
        help_text=(
            "Weighted sum of the above components, per "
            "settings.RANKING_COMPONENT_WEIGHTS. Higher is better."
        ),
    )

    rank = models.PositiveIntegerField(
        help_text=(
            "1-indexed rank within this workflow_run, by "
            "final_score descending."
        ),
    )

    explanation = models.TextField(
        blank=True,
        help_text="Human-readable breakdown of the score.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        unique_together = ("workflow_run", "protein")
        ordering = ["rank"]

    def __str__(self):
        return (
            f"#{self.rank} {self.protein.protein_id} "
            f"({round(self.final_score, 3)})"
        )
