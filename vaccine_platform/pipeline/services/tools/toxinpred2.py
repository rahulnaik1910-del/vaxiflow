import subprocess
from pathlib import Path

from django.conf import settings


class ToxinPred2Executor:
    """
    Runs ToxinPred2 (Raghava lab), a genuinely pip-installable and
    verified-working toxicity classifier - unlike VaxiJen/AllerTOP/
    Phobius, this needs no fallback.
    """

    TOXINPRED2_EXECUTABLE = settings.TOXINPRED2_EXECUTABLE

    @staticmethod
    def write_query_fasta(proteins, output_dir):
        """
        proteins: list of Protein instances.
        Uses protein.protein_id as the FASTA header, matching the
        ID column in ToxinPred2's CSV output.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fasta_file = output_dir / "toxinpred2_query.fasta"

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

        output_file = output_dir / "toxinpred2_results.csv"

        command = [
            ToxinPred2Executor.TOXINPRED2_EXECUTABLE,
            "-i",
            str(query_fasta),
            "-o",
            str(output_file),
            "-t",
            settings.TOXINPRED2_THRESHOLD,
            "-m",
            settings.TOXINPRED2_MODEL,
            "-d",
            "2",  # display all peptides, not just predicted toxins
        ]

        print("=" * 70)
        print("TOXINPRED2 EXECUTOR STARTED")
        print(" ".join(command))
        print("=" * 70)

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch toxinpred2")
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
