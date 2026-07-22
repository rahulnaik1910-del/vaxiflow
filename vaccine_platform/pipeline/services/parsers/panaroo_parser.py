import csv
import re
from pathlib import Path


class PanarooParser:
    """
    Parses Panaroo's gene_presence_absence.csv output.

    The file has a fixed set of metadata columns, followed by one
    column per input genome (named after the GFF3 filename Panaroo
    was given, minus the extension - in our case this is always
    "genome_{genome_id}_annotation" since that's the prefix
    BaktaExecutor uses). Each cell under a genome column holds zero,
    one, or more protein/locus IDs for that gene in that genome
    (Panaroo separates multiple paralogs with ';' or tabs).
    """

    # Columns Panaroo always writes before the per-genome columns.
    METADATA_COLUMNS = {
        "Gene",
        "Non-unique Gene name",
        "Annotation",
        "No. isolates",
        "No. sequences",
        "Avg sequences per isolate",
        "Genome Fragment",
        "Order within Fragment",
        "Accessory Fragment",
        "Accessory Order within Fragment",
        "QC",
        "Min group size nuc",
        "Max group size nuc",
        "Avg group size nuc",
    }

    GENOME_COLUMN_PATTERN = re.compile(r"genome_(\d+)_annotation")

    def __init__(self, csv_file):
        self.csv_file = Path(csv_file)

    def parse(self):
        """
        Returns a list of dicts, one per gene cluster:
            [
                {
                    "cluster_name": "dnaA",
                    "annotation": "Chromosomal replication initiator...",
                    "genome_count": 3,
                    "members": [
                        {"genome_id": 1, "protein_id": "genome_1_annotation_00001"},
                        {"genome_id": 2, "protein_id": "genome_2_annotation_00007"},
                        ...
                    ],
                },
                ...
            ]
        """
        clusters = []

        if not self.csv_file.exists():
            return clusters

        with open(self.csv_file, newline="") as handle:

            reader = csv.DictReader(handle)

            genome_columns = [
                column
                for column in (reader.fieldnames or [])
                if column not in self.METADATA_COLUMNS
                and column != "Gene"
            ]

            for row in reader:

                members = []

                for column in genome_columns:

                    cell = (row.get(column) or "").strip()

                    if not cell:
                        continue

                    match = self.GENOME_COLUMN_PATTERN.search(column)

                    if not match:
                        # Column doesn't follow our expected naming
                        # convention (e.g. Panaroo run outside this
                        # pipeline) - skip rather than guess.
                        continue

                    genome_id = int(match.group(1))

                    protein_ids = re.split(r"[;\t]", cell)

                    for protein_id in protein_ids:

                        protein_id = protein_id.strip()

                        if protein_id:
                            members.append(
                                {
                                    "genome_id": genome_id,
                                    "protein_id": protein_id,
                                }
                            )

                genomes_present = {m["genome_id"] for m in members}

                clusters.append(
                    {
                        "cluster_name": row.get("Gene", "").strip(),
                        "annotation": row.get(
                            "Annotation", ""
                        ).strip(),
                        "genome_count": len(genomes_present),
                        "members": members,
                    }
                )

        return clusters
