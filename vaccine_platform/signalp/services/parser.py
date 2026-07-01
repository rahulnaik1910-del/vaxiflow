from pathlib import Path


class SignalPParser:
    """
    Parses SignalP prediction output.
    """

    @staticmethod
    def parse(result_file: Path):
        """
        Parse SignalP output.

        Returns
        -------
        list[dict]
        """

        predictions = []

        #
        # Placeholder implementation.
        #
        # This will be replaced after
        # SignalP is installed and we know
        # the exact output format.
        #

        if not result_file.exists():

            return predictions

        return predictions
    