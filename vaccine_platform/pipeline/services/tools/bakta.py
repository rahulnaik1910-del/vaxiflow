import subprocess
from pathlib import Path

from django.conf import settings

from users.validators import (
    validate_nucleotide_fasta,
)


class BaktaExecutor:
    """
    Executes Bakta Light for bacterial genome annotation.
    """

    BAKTA_EXECUTABLE = (
        "/home/rahul/miniconda3/"
        "envs/vaxiflow/bin/bakta"
    )

    BAKTA_DB = (
        "/mnt/d/VaxiFlowData/"
        "bakta-light/db-light"
    )

    @staticmethod
    def run(genome, workflow_run):
        """
        Run Bakta Light on one uploaded genome.

        Returns:
            dict containing:
                - exit_code
                - log
                - output_directory
        """

        genome_path = Path(
            genome.genome_file.path
        )

        is_valid, validation_message = (
            validate_nucleotide_fasta(
                genome_path
            )
        )

        if not is_valid:

            return {
                "exit_code": 1,
                "log": (
                    "Bakta input validation failed.\n"
                    f"Genome ID: {genome.id}\n"
                    f"File: {genome_path}\n"
                    f"Reason: {validation_message}"
                ),
                "output_directory": "",
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

        prefix = (
            f"genome_{genome.id}_annotation"
        )

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

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except OSError as exc:

            return {
                "exit_code": 1,
                "log": (
                    "Failed to start Bakta.\n"
                    f"Genome ID: {genome.id}\n"
                    f"Input: {genome_path}\n"
                    f"Error: {exc}"
                ),
                "output_directory": str(
                    output_dir
                ),
            }

        log = (
            f"Genome ID: {genome.id}\n"
            f"Input: {genome_path}\n"
            f"Output: {output_dir}\n"
            f"Validation: {validation_message}\n\n"
            f"Command: {' '.join(command)}\n\n"
            f"STDOUT:\n"
            f"{result.stdout}\n\n"
            f"STDERR:\n"
            f"{result.stderr}"
        )

        return {
            "exit_code": result.returncode,
            "log": log,
            "output_directory": str(
                output_dir
            ),
        }
    