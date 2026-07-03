from pathlib import Path

from proteins.models import Protein


class ProteinExporter:
    """
    Exports a protein sequence into FASTA format.
    """

    @staticmethod
    def export(protein: Protein, output_directory: Path):

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        fasta_file = output_directory / "query.fasta"

        with open(fasta_file, "w") as handle:

            handle.write(
                f">{protein.protein_id}\n"
            )

            sequence = protein.sequence

            for i in range(0, len(sequence), 60):

                handle.write(
                    sequence[i:i + 60] + "\n"
                )

        return fasta_file
    