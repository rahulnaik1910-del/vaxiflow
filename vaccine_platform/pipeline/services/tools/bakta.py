import subprocess
import time
from pathlib import Path

from django.conf import settings

from users.validators import validate_nucleotide_fasta


class BaktaExecutor:

    BAKTA_EXECUTABLE = settings.BAKTA_EXECUTABLE

    BAKTA_DB = settings.BAKTA_DB

    @staticmethod
    def run(genome, workflow_run):

        print("=" * 70)
        print("BAKTA EXECUTOR STARTED")

        genome_path = Path(genome.genome_file.path)

        print(f"Genome path : {genome_path}")

        is_valid, validation_message = validate_nucleotide_fasta(
            genome_path
        )

        print(f"Validation : {is_valid}")

        if not is_valid:

            print("Genome validation failed")

            return {
                "exit_code": 1,
                "log": validation_message,
                "output_directory": "",
                "prefix": "",
            }

        output_dir = (
            Path(settings.MEDIA_ROOT)
            / "pipeline_runs"
            / f"run_{workflow_run.id}"
            / "bakta"
            / f"genome_{genome.id}"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Output dir : {output_dir}")

        prefix = f"genome_{genome.id}_annotation"

        command = [
            BaktaExecutor.BAKTA_EXECUTABLE,
            "--db",
            BaktaExecutor.BAKTA_DB,
            "--output",
            str(output_dir),
            "--prefix",
            prefix,
            "--force",
            "--skip-sorf",
            str(genome_path),
        ]

        print("Command:")
        print(" ".join(command))
        print("=" * 70)
        print("Starting Bakta...")
        start = time.time()

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch Bakta")
            print(repr(e))

            return {
                "exit_code": 1,
                "log": str(e),
                "output_directory": str(output_dir),
                "prefix": prefix,
            }

        elapsed = round(time.time() - start, 2)

        print("=" * 70)
        print(f"Bakta finished in {elapsed} seconds")
        print(f"Exit code : {result.returncode}")
        print("=" * 70)

        log = (
            f"STDOUT\n\n{result.stdout}\n\n"
            f"STDERR\n\n{result.stderr}"
        )

        return {
            "exit_code": result.returncode,
            "log": log,
            "output_directory": str(output_dir),
            "prefix": prefix,
        }
    