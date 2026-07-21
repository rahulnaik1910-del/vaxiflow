from pathlib import Path


class FAAParser:
    """
    Parses a Bakta .faa protein FASTA file.

    Each Bakta protein FASTA header looks like:

        >genome_1_annotation_00001 hypothetical protein
        >genome_1_annotation_00002 DNA polymerase III subunit alpha

    i.e. ">" + protein_id + " " + product description.
    """

    def __init__(self, faa_file):
        self.faa_file = Path(faa_file)

    def parse(self):
        """
        Read the FAA file and return a list of dicts:
            [{"protein_id": ..., "product": ..., "sequence": ...}, ...]
        """
        proteins = []

        if not self.faa_file.exists():
            return proteins

        protein_id = None
        product = ""
        sequence_lines = []

        def flush():
            if protein_id is not None:
                proteins.append(
                    {
                        "protein_id": protein_id,
                        "product": product,
                        "sequence": "".join(sequence_lines),
                    }
                )

        with open(self.faa_file, "r") as handle:

            for raw_line in handle:

                line = raw_line.rstrip("\n").rstrip("\r")

                if not line:
                    continue

                if line.startswith(">"):

                    flush()

                    header = line[1:]
                    parts = header.split(" ", 1)

                    protein_id = parts[0].strip()
                    product = parts[1].strip() if len(parts) > 1 else ""
                    sequence_lines = []

                else:
                    sequence_lines.append(line.strip())

        flush()

        return proteins
