from django.conf import settings

from pipeline.models import DegHit
from pipeline.services.parsers.deg_parser import DegParser


class DegImporter:

    @staticmethod
    def import_results(
        representative_proteins,
        output_file,
    ):
        """
        representative_proteins: dict {cluster_id: (GeneCluster, Protein)}
                                  - the exact set of core clusters
                                  screened, so clusters with no hit at
                                  all are still recorded as
                                  not-essential rather than silently
                                  skipped.
        output_file:              str/Path - the deg_hits.tsv file
                                  written by DegExecutor

        Returns a dict:
            {
                "screened": <int>,
                "essential": <int>,
                "not_essential": <int>,
                "log": <str>,
            }
        """

        hits = DegParser(output_file).parse()

        log_lines = [
            f"Parsed {len(hits)} raw BLAST hits from {output_file}.",
            f"Screening {len(representative_proteins)} core gene "
            "clusters against DEG.",
            "Thresholds: "
            f"identity >= {settings.DEG_MIN_IDENTITY}%, "
            f"e-value <= {settings.DEG_MAX_EVALUE}, "
            f"coverage >= {settings.DEG_MIN_COVERAGE}%.",
        ]

        essential_count = 0
        not_essential_count = 0

        for cluster_id, (
            gene_cluster,
            representative_protein,
        ) in representative_proteins.items():

            hit = hits.get(cluster_id)

            is_essential = False
            coverage = None

            if hit is not None and representative_protein.length:

                coverage = (
                    hit["alignment_length"]
                    / representative_protein.length
                ) * 100

                is_essential = (
                    hit["identity"] >= settings.DEG_MIN_IDENTITY
                    and hit["evalue"] <= settings.DEG_MAX_EVALUE
                    and coverage >= settings.DEG_MIN_COVERAGE
                )

            DegHit.objects.update_or_create(
                gene_cluster=gene_cluster,
                defaults={
                    "representative_protein": (
                        representative_protein
                    ),
                    "subject_id": (
                        hit["subject_id"] if hit else ""
                    ),
                    "identity": hit["identity"] if hit else None,
                    "alignment_length": (
                        hit["alignment_length"] if hit else None
                    ),
                    "coverage": coverage,
                    "evalue": hit["evalue"] if hit else None,
                    "bit_score": hit["bit_score"] if hit else None,
                },
            )

            gene_cluster.is_essential = is_essential
            gene_cluster.save(update_fields=["is_essential"])

            if is_essential:
                essential_count += 1
            else:
                not_essential_count += 1

        log_lines.append(
            f"Result: {essential_count} essential, "
            f"{not_essential_count} not essential."
        )

        return {
            "screened": len(representative_proteins),
            "essential": essential_count,
            "not_essential": not_essential_count,
            "log": "\n".join(log_lines),
        }
