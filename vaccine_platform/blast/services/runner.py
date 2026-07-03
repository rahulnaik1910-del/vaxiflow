import subprocess
from pathlib import Path


class BlastRunner:
    """
    Executes BLASTP against the local human database.
    """

    @staticmethod
    def run(
        query_fasta: Path,
        database: Path,
        output_directory: Path,
    ):

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = output_directory / "blast_results.xml"

        command = [

            "blastp",

            "-query",
            str(query_fasta),

            "-db",
            str(database),

            "-out",
            str(output_file),

            "-outfmt",
            "5",

            "-evalue",
            "1e-5",

            "-max_target_seqs",
            "10",

        ]

        subprocess.run(
            command,
            check=True,
        )

        return output_file
    