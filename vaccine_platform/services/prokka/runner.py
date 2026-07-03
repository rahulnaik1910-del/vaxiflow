import subprocess
from pathlib import Path


class ProkkaRunner:
    """
    Execute Prokka directly inside WSL.
    """

    def __init__(self, analysis):

        self.analysis = analysis
        self.genome = analysis.genome

    def run(self):

        try:

            print("\n==============================")
            print("PROKKA RUNNER STARTED")
            print("==============================")

            print("A - Creating output directory object")

            output_dir = (
                Path("media")
                / "annotations"
                / f"analysis_{self.analysis.id}"
            )

            print("B - Output directory object created")

            output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            print("C - Output directory created")

            print("Output Directory:")
            print(output_dir.resolve())

            genome_path = Path(
                self.genome.genome_file.path
            ).resolve()

            print("D - Genome path resolved")

            print("Genome File:")
            print(genome_path)

            command = [
                "prokka",
                "--force",
                "--outdir",
                str(output_dir.resolve()),
                "--prefix",
                "annotation",
                str(genome_path),
            ]

            print("E - Command prepared")

            print("\nRunning Command:\n")
            print(" ".join(command))
            print()

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            print("F - Prokka finished")

            print("Return Code:", result.returncode)

            print("\n========== STDOUT ==========")
            print(result.stdout)

            print("\n========== STDERR ==========")
            print(result.stderr)

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_directory": str(output_dir),
            }

        except Exception as error:

            print("\n====================================")
            print("EXCEPTION INSIDE PROKKA RUNNER")
            print("====================================")
            print(type(error))
            print(error)

            raise
        