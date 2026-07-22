import subprocess
from pathlib import Path

from django.conf import settings


class DegExecutor:
    """
    Runs BLASTP of a set of representative core-genome protein
    sequences against the local Database of Essential Genes (DEG).
    """

    BLASTP_EXECUTABLE = settings.DEG_BLASTP_EXECUTABLE

    DEG_DATABASE = settings.DEG_DATABASE

    @staticmethod
    def write_query_fasta(representative_proteins, output_dir):
        """
        representative_proteins: list of (cluster_id, Protein)
        Returns the path to the FASTA file written.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fasta_file = output_dir / "core_representatives.fasta"

        with open(fasta_file, "w") as handle:

            for cluster_id, protein in representative_proteins:

                # Use the cluster ID as the query name (not the
                # protein_id) so results map straight back to a
                # GeneCluster without a second lookup table.
                handle.write(f">cluster_{cluster_id}\n")

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

        output_file = output_dir / "deg_hits.tsv"

        # Tabular output (outfmt 6) is used instead of XML since we
        # only need the best hit per query and this is simpler to
        # parse and test than BLAST XML.
        columns = (
            "qseqid sseqid pident length mismatch gapopen "
            "qstart qend sstart send evalue bitscore"
        )

        command = [
            DegExecutor.BLASTP_EXECUTABLE,
            "-query",
            str(query_fasta),
            "-db",
            DegExecutor.DEG_DATABASE,
            "-out",
            str(output_file),
            "-outfmt",
            f"6 {columns}",
            "-evalue",
            "1e-5",
            "-max_target_seqs",
            "1",
        ]

        print("=" * 70)
        print("DEG EXECUTOR STARTED")
        print(" ".join(command))
        print("=" * 70)

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

        except Exception as e:

            print("Failed to launch blastp for DEG screening")
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
