from pathlib import Path


class ProkkaParser:
    """
    Reads Prokka output files.
    """

    def __init__(self, output_directory):

        self.output_directory = Path(output_directory)

    def gff(self):

        files = list(self.output_directory.glob("*.gff"))

        return files[0] if files else None

    def faa(self):

        files = list(self.output_directory.glob("*.faa"))

        return files[0] if files else None

    def gbk(self):

        files = list(self.output_directory.glob("*.gbk"))

        return files[0] if files else None

    def ffn(self):

        files = list(self.output_directory.glob("*.ffn"))

        return files[0] if files else None
    