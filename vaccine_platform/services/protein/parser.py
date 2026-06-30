from pathlib import Path


class ProteinParser:
    """
    Parses Prokka .faa files and extracts proteins.
    """

    def __init__(self, faa_file):

        self.faa_file = Path(faa_file)

    def parse(self):

        proteins = []

        if not self.faa_file.exists():

            raise FileNotFoundError(
                f"{self.faa_file} does not exist."
            )

        header = None
        sequence = []

        with open(self.faa_file, "r") as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                if line.startswith(">"):

                    if header:

                        proteins.append(
                            self.build_protein(
                                header,
                                sequence,
                            )
                        )

                    header = line[1:]
                    sequence = []

                else:

                    sequence.append(line)

            if header:

                proteins.append(
                    self.build_protein(
                        header,
                        sequence,
                    )
                )

        return proteins

    def build_protein(self, header, sequence):

        sequence = "".join(sequence)

        parts = header.split(maxsplit=1)

        protein_id = parts[0]

        product = ""

        if len(parts) > 1:

            product = parts[1]

        return {

            "protein_id": protein_id,

            "product": product,

            "sequence": sequence,

            "length": len(sequence),

        }
    