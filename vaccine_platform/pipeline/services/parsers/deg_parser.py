from pathlib import Path


class DegParser:
    """
    Parses BLASTP tabular output (outfmt 6) produced by DegExecutor.

    Columns (in order):
        qseqid sseqid pident length mismatch gapopen
        qstart qend sstart send evalue bitscore

    Since -max_target_seqs 1 is used, there is normally at most one
    line per query, but this parser is defensive and keeps only the
    best (lowest e-value) hit per query in case that ever changes.
    """

    def __init__(self, tsv_file):
        self.tsv_file = Path(tsv_file)

    def parse(self):
        """
        Returns a dict keyed by cluster_id (int, parsed out of the
        "cluster_<id>" query name written by DegExecutor):
            {
                12: {
                    "subject_id": "DEG10140123",
                    "identity": 45.2,
                    "alignment_length": 210,
                    "evalue": 1.2e-40,
                    "bit_score": 180.0,
                },
                ...
            }
        """

        hits = {}

        if not self.tsv_file.exists():
            return hits

        with open(self.tsv_file, "r") as handle:

            for raw_line in handle:

                line = raw_line.strip()

                if not line:
                    continue

                columns = line.split("\t")

                if len(columns) < 12:
                    continue

                query_name = columns[0]

                if not query_name.startswith("cluster_"):
                    continue

                try:
                    cluster_id = int(
                        query_name.replace("cluster_", "", 1)
                    )
                except ValueError:
                    continue

                hit = {
                    "subject_id": columns[1],
                    "identity": float(columns[2]),
                    "alignment_length": int(columns[3]),
                    "evalue": float(columns[10]),
                    "bit_score": float(columns[11]),
                }

                existing = hits.get(cluster_id)

                if (
                    existing is None
                    or hit["evalue"] < existing["evalue"]
                ):
                    hits[cluster_id] = hit

        return hits
