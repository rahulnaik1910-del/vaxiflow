from services.analysis.base import BaseAnalysisService

from signalp.services.runner import SignalPRunner
from signalp.services.parser import SignalPParser
from signalp.services.importer import SignalPImporter


class SignalPService(BaseAnalysisService):
    """
    Main orchestration service for SignalP.
    """

    def __init__(self, fasta_file, output_directory):
        self.fasta_file = fasta_file
        self.output_directory = output_directory

    def validate(self):
        """
        Validate inputs before execution.
        """
        if not self.fasta_file.exists():
            raise FileNotFoundError(
                f"Protein FASTA not found: {self.fasta_file}"
            )

    def run(self):
        """
        Execute SignalP.
        """
        return SignalPRunner.run(
            fasta_file=self.fasta_file,
            output_directory=self.output_directory,
        )

    def parse(self, output):
        """
        Parse SignalP output.
        """
        result_file = output / "prediction_results.txt"

        return SignalPParser.parse(result_file)

    def import_results(self, parsed):
        """
        Save parsed predictions.
        """
        return SignalPImporter.import_results(parsed)
    