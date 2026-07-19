from pathlib import Path


class FAAParser:
    def __init__(self, faa_file):
        self.faa_file = Path(faa_file)

    def parse(self):
        proteins = []

        current_protein = None
        sequence = []

        with open(self.faa_file, "r", encoding="utf-8") as f:

            for line in f:
                line = line.strip()

                if not line:
                    continue

                if line.startswith(">"):

                    if current_protein is not None:
                        proteins.append(
                            {
                                "protein_id": current_protein,
                                "sequence": "".join(sequence),
                            }
                        )

                    header = line[1:]
                    current_protein = header.split()[0]
                    sequence = []

                else:
                    sequence.append(line)

            if current_protein is not None:
                proteins.append(
                    {
                        "protein_id": current_protein,
                        "sequence": "".join(sequence),
                    }
                )

        return proteins
    