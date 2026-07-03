from pathlib import Path
import subprocess
import tempfile


class SignalPRunner:
    """
    Executes SignalP on a protein FASTA file.

    This class is responsible only for
    launching SignalP.

    It does NOT parse results.
    """

    @staticmethod
    def run(
        fasta_file: Path,
        output_directory: Path,
    ) -> Path:
        """
        Execute SignalP.

        Returns
        -------
        Path
            Output directory.
        """

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        #
        # Placeholder
        #
        # Later we will replace this
        # with the real SignalP command.
        #

        return output_directory
    