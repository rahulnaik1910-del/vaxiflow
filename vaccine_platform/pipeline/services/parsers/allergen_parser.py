from pathlib import Path


class AllergenParser:
    """
    Parses BLASTP tabular output (outfmt 6) produced by
    AllergenExecutor, keyed directly by protein_id (the query name
    written by AllergenExecutor.write_query_fasta).

    Columns: qseqid sseqid pident length mismatch gapopen
             qstart qend sstart send evalue bitscore
    """

    def __init__(self, tsv_file):
        self.tsv_file = Path(tsv_file)

    def parse(self):
        """
        Returns a dict keyed by protein_id, keeping only the best
        (lowest e-value) hit per query:
            {
                "protein_1": {
                    "subject_id": "AllergenOnline_00123",
                    "identity": 42.5,
                    "alignment_length": 95,
                    "evalue": 3.1e-30,
                    "bit_score": 140.0,
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

                protein_id = columns[0]

                hit = {
                    "subject_id": columns[1],
                    "identity": float(columns[2]),
                    "alignment_length": int(columns[3]),
                    "evalue": float(columns[10]),
                    "bit_score": float(columns[11]),
                }

                existing = hits.get(protein_id)

                if (
                    existing is None
                    or hit["evalue"] < existing["evalue"]
                ):
                    hits[protein_id] = hit

        return hits
