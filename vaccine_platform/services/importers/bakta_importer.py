from pathlib import Path

from pipeline.services.parsers.faa_parser import FAAParser
from pipeline.services.parsers.gff3_parser import GFF3Parser


class BaktaImporter:
    def __init__(self, gff3_file, faa_file):
        self.gff3_file = Path(gff3_file)
        self.faa_file = Path(faa_file)

    def parse(self):
        gff3_records = GFF3Parser(self.gff3_file).parse()
        faa_records = FAAParser(self.faa_file).parse()

        sequence_map = {
            protein["protein_id"]: protein["sequence"]
            for protein in faa_records
        }

        merged_proteins = []

        for protein in gff3_records:
            merged_proteins.append(
                {
                    **protein,
                    "sequence": sequence_map.get(protein["protein_id"]),
                }
            )

        return merged_proteins
    