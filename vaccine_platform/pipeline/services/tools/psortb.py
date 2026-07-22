import subprocess
from pathlib import Path

from django.conf import settings

# Maps Project.gram_stain values to the psort CLI flag.
GRAM_STAIN_FLAGS = {
    "negative": "-n",
    "positive": "-p",
    "archaea": "-a",
}


class PsortbExecutor:

    PSORTB_EXECUTABLE = settings.PSORTB_EXECUTABLE

    @staticmethod
    def write_query_fasta(proteins, output_dir):
        """
        proteins: list of Protein instances.
        Uses protein.protein_id as the FASTA header, since that's
        what comes back in PSORTb's SeqID column.

        Returns the path to the FASTA file written.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fasta_file = output_dir / "psortb_query.fasta"

        with open(fasta_file, "w") as handle:

            for protein in proteins:

                handle.write(f">{protein.protein_id}\n")

                sequence = protein.sequence

                for i in range(0, len(sequence), 60):
                    handle.write(sequence[i:i + 60] + "\n")

        return fasta_file

    @staticmethod
    def run(query_fasta, output_dir, gram_stain):
        """
        gram_stain: one of "negative", "positive", "archaea"
                    (Project.gram_stain).

        Returns a dict:
            {
                "exit_code": <int>,
                "log": <str>,
                "output_file": <str>,
            }
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "psortb_terse.tsv"

        gram_flag = GRAM_STAIN_FLAGS.get(gram_stain)

        if gram_flag is None:

            message = (
                f"Unknown gram_stain '{gram_stain}' - expected one "
                f"of {list(GRAM_STAIN_FLAGS.keys())}."
            )

            return {
                "exit_code": 1,
                "log": message,
                "output_file": str(output_file),
            }

        command = [
            PsortbExecutor.PSORTB_EXECUTABLE,
            gram_flag,
            "-o",
            "terse",
            str(query_fasta),
        ]

        print("=" * 70)
        print("PSORTB EXECUTOR STARTED")
        print(" ".join(command))
        print("=" * 70)

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch psort")
            print(repr(e))

            return {
                "exit_code": 1,
                "log": str(e),
                "output_file": str(output_file),
            }

        # psort writes terse output to stdout, not to a file, so we
        # capture it ourselves.
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
