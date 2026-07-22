from pathlib import Path

from django.conf import settings

from proteins.models import Protein
from users.models import Genome

from pipeline.models import GeneCluster, GeneClusterMember
from pipeline.services.parsers.panaroo_parser import PanarooParser

# Standard core-genome threshold used by Panaroo/Roary: a gene is
# considered "core" if present in at least this fraction of genomes.
CORE_GENOME_THRESHOLD = 0.95


class PanarooImporter:

    @staticmethod
    def import_from_output(panaroo_run, output_dir, total_genomes):
        """
        panaroo_run:    pipeline.models.PanarooRun
        output_dir:     str or Path - directory Panaroo wrote its
                        output to
        total_genomes:  int - number of genomes included in this run,
                        used to decide core vs accessory

        Returns a dict:
            {
                "cluster_count": <int>,
                "core_count": <int>,
                "accessory_count": <int>,
                "unmatched_proteins": <int>,
                "log": <str>,
            }
        """

        output_dir = Path(output_dir)

        csv_file = (
            output_dir
            / "gene_presence_absence.csv"
        )

        log_lines = [
            f"Looking for Panaroo output in: {output_dir}",
            f"gene_presence_absence.csv exists="
            f"{csv_file.exists()}",
        ]

        if not csv_file.exists():
            log_lines.append(
                "No gene_presence_absence.csv found - "
                "nothing to import."
            )
            return {
                "cluster_count": 0,
                "core_count": 0,
                "accessory_count": 0,
                "unmatched_proteins": 0,
                "log": "\n".join(log_lines),
            }

        parsed_clusters = PanarooParser(csv_file).parse()

        log_lines.append(
            f"Parsed {len(parsed_clusters)} gene clusters."
        )

        core_count = 0
        accessory_count = 0
        unmatched_proteins = 0

        # Cache Genome and Protein lookups to avoid a query per row.
        genome_cache = {
            genome.id: genome
            for genome in Genome.objects.all()
        }

        protein_cache = {
            protein.protein_id: protein
            for protein in Protein.objects.all()
        }

        for cluster_data in parsed_clusters:

            is_core = (
                cluster_data["genome_count"] / total_genomes
                >= CORE_GENOME_THRESHOLD
                if total_genomes > 0
                else False
            )

            if is_core:
                core_count += 1
            else:
                accessory_count += 1

            gene_cluster = GeneCluster.objects.create(
                panaroo_run=panaroo_run,
                cluster_name=cluster_data["cluster_name"]
                or "unnamed",
                is_core=is_core,
                genome_count=cluster_data["genome_count"],
            )

            member_objects = []

            for member in cluster_data["members"]:

                genome = genome_cache.get(member["genome_id"])

                if genome is None:
                    continue

                protein = protein_cache.get(member["protein_id"])

                if protein is None:
                    unmatched_proteins += 1

                member_objects.append(
                    GeneClusterMember(
                        gene_cluster=gene_cluster,
                        genome=genome,
                        protein=protein,
                    )
                )

            GeneClusterMember.objects.bulk_create(member_objects)

        log_lines.append(
            f"Imported {len(parsed_clusters)} gene clusters "
            f"({core_count} core, {accessory_count} accessory). "
            f"{unmatched_proteins} memberships could not be matched "
            "to an imported Protein row."
        )

        return {
            "cluster_count": len(parsed_clusters),
            "core_count": core_count,
            "accessory_count": accessory_count,
            "unmatched_proteins": unmatched_proteins,
            "log": "\n".join(log_lines),
        }
