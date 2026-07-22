import subprocess
import time
from pathlib import Path

from django.conf import settings


class PanarooExecutor:

    PANAROO_EXECUTABLE = settings.PANAROO_EXECUTABLE

    @staticmethod
    def run(gff3_paths, output_dir, panaroo_run):
        """
        gff3_paths:   list of Path/str - one Bakta .gff3 file per genome
        output_dir:   Path - where Panaroo should write its results
        panaroo_run:  pipeline.models.PanarooRun - only used for
                      context in logging.

        Returns a dict:
            {
                "exit_code": <int>,
                "log": <str>,
                "output_directory": <str>,
            }
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 70)
        print("PANAROO EXECUTOR STARTED")
        print(f"Genomes (GFF3 files): {len(gff3_paths)}")
        print(f"Output dir : {output_dir}")

        missing = [
            str(p) for p in gff3_paths if not Path(p).exists()
        ]

        if missing:

            message = (
                "One or more Bakta GFF3 files are missing:\n"
                + "\n".join(missing)
            )

            print(message)

            return {
                "exit_code": 1,
                "log": message,
                "output_directory": str(output_dir),
            }

        command = (
            [
                PanarooExecutor.PANAROO_EXECUTABLE,
                "-i",
            ]
            + [str(p) for p in gff3_paths]
            + [
                "-o",
                str(output_dir),
                "--clean-mode",
                "strict",
            ]
        )

        print("Command:")
        print(" ".join(command))
        print("=" * 70)
        print("Starting Panaroo...")
        start = time.time()

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch Panaroo")
            print(repr(e))

            return {
                "exit_code": 1,
                "log": str(e),
                "output_directory": str(output_dir),
            }

        elapsed = round(time.time() - start, 2)

        print("=" * 70)
        print(f"Panaroo finished in {elapsed} seconds")
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
        }
