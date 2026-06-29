import subprocess
import shutil
from pathlib import Path


class ProkkaRunner:
    """
    Handles execution of Prokka.
    """

    def __init__(self):

        self.prokka_path = shutil.which("prokka")

    def is_installed(self):
        """
        Check whether Prokka is installed.
        """

        return self.prokka_path is not None

    def get_version(self):
        """
        Return installed Prokka version.
        """

        if not self.is_installed():

            return None

        result = subprocess.run(
            ["prokka", "--version"],
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()

    def run_annotation(
        self,
        genome_file,
        output_directory,
        prefix,
    ):
        """
        Run Prokka annotation.
        """

        if not self.is_installed():

            return {
                "success": False,
                "message": "Prokka is not installed.",
            }

        command = [
            "prokka",
            genome_file,
            "--outdir",
            output_directory,
            "--prefix",
            prefix,
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e),
            }
        