import subprocess
from pathlib import Path


class ProkkaRunner:
    """
    Execute Prokka through WSL.
    """

    def __init__(self, analysis):

        self.analysis = analysis
        self.genome = analysis.genome

    def windows_to_wsl(self, path: Path):

        windows_path = str(path.resolve())

        drive = windows_path[0].lower()

        remaining = windows_path[2:].replace("\\", "/")

        return f"/mnt/{drive}{remaining}"

    def run(self):

        output_dir = (
            Path("media")
            / "annotations"
            / f"analysis_{self.analysis.id}"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        genome_path = self.windows_to_wsl(
            Path(self.genome.genome_file.path)
        )

        output_path = self.windows_to_wsl(
            output_dir.resolve()
        )

        command = [
            "wsl",
            "prokka",
            "--force",
            "--outdir",
            output_path,
            "--prefix",
            "annotation",
            genome_path,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output_directory": str(output_dir),
        }
    