import subprocess
from pathlib import Path

from django.conf import settings


class PhobiusExecutor:
    """
    Runs Phobius (signal peptide + transmembrane topology
    prediction) in "short" tabular output mode.

    NOTE: Phobius is a licensed academic tool (Stockholm University,
    phobius.sbc.su.se) with no apt/pip package - it must be
    downloaded and registered for separately and PHOBIUS_EXECUTABLE
    pointed at the installed phobius.pl. This executor's command
    construction follows Phobius's documented usage
    (`phobius.pl -short <fasta>`), but has not been run against the
    real binary in this environment.
    """

    PHOBIUS_EXECUTABLE = settings.PHOBIUS_EXECUTABLE

    @staticmethod
    def write_query_fasta(proteins, output_dir):
        """
        proteins: list of Protein instances.
        Uses protein.protein_id as the FASTA header, matching what
        comes back in Phobius's SEQENCE_ID column.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fasta_file = output_dir / "phobius_query.fasta"

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

        output_file = output_dir / "phobius_short.txt"

        command = [
            PhobiusExecutor.PHOBIUS_EXECUTABLE,
            "-short",
            str(query_fasta),
        ]

        print("=" * 70)
        print("PHOBIUS EXECUTOR STARTED")
        print(" ".join(command))
        print("=" * 70)

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch phobius")
            print(repr(e))

            return {
                "exit_code": 1,
                "log": str(e),
                "output_file": str(output_file),
            }

        # Phobius -short writes its table to stdout.
        with open(output_file, "w") as handle:
            handle.write(result.stdout)

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
