import subprocess
from pathlib import Path

from django.conf import settings


class AllergenExecutor:
    """
    Runs BLASTP of candidate proteins against a curated allergen
    database (e.g. AllergenOnline), for the FAO/WHO homology-based
    allergenicity screening criteria.
    """

    BLASTP_EXECUTABLE = settings.ALLERGEN_BLASTP_EXECUTABLE

    ALLERGEN_DATABASE = settings.ALLERGEN_DATABASE

    @staticmethod
    def write_query_fasta(proteins, output_dir):
        """
        proteins: list of Protein instances.
        Uses protein.protein_id as the FASTA header.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fasta_file = output_dir / "allergen_query.fasta"

        with open(fasta_file, "w") as handle:

            for protein in proteins:

                handle.write(f">{protein.protein_id}\n")

                sequence = protein.sequence

                for i in range(0, len(sequence), 60):
                    handle.write(sequence[i:i + 60] + "\n")

        return fasta_file

    @staticmethod
    def run(query_fasta, output_dir):
        """
        Returns a dict:
            {
                "exit_code": <int>,
                "log": <str>,
                "output_file": <str>,
            }
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "allergen_hits.tsv"

        columns = (
            "qseqid sseqid pident length mismatch gapopen "
            "qstart qend sstart send evalue bitscore"
        )

        command = [
            AllergenExecutor.BLASTP_EXECUTABLE,
            "-query",
            str(query_fasta),
            "-db",
            AllergenExecutor.ALLERGEN_DATABASE,
            "-out",
            str(output_file),
            "-outfmt",
            f"6 {columns}",
            "-evalue",
            "1e-5",
            "-max_target_seqs",
            "1",
        ]

        print("=" * 70)
        print("ALLERGEN EXECUTOR STARTED")
        print(" ".join(command))
        print("=" * 70)

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch blastp for allergen screening")
            print(repr(e))

            return {
                "exit_code": 1,
                "log": str(e),
                "output_file": str(output_file),
            }

        log = (
            f"STDOUT\n\n{result.stdout}\n\n"
            f"STDERR\n\n{result.stderr}"
        )

        print(f"Exit code: {result.returncode}")

        return {
            "exit_code": result.returncode,
            "log": log,
            "output_file": str(output_file),
        }
