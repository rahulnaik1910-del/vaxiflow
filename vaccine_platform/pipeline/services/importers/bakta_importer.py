from pathlib import Path

from pipeline.services.parsers.faa_parser import FAAParser
from pipeline.services.parsers.gff3_parser import GFF3Parser
from protein.models import Protein


class BaktaImporter:
    def __init__(self, analysis, gff3_file, faa_file):
        self.analysis = analysis
        self.gff3_file = Path(gff3_file)
        self.faa_file = Path(faa_file)

    def parse(self):
        gff3_records = GFF3Parser(self.gff3_file).parse()
        faa_records = FAAParser(self.faa_file).parse()

        sequence_map = {
            protein["protein_id"]: protein["sequence"]
            for protein in faa_records
        }

        merged = []

        for protein in gff3_records:
            merged.append(
                {
                    **protein,
                    "sequence": sequence_map.get(protein["protein_id"], ""),
                }
            )

        return merged

    def save(self):
        proteins = self.parse()

        objects = []

        for protein in proteins:
            sequence = protein["sequence"]

            objects.append(
                Protein(
                    analysis=self.analysis,
                    protein_id=protein["protein_id"],
                    gene=protein["gene"] or "",
                    product=protein["product"] or "",
                    sequence=sequence,
                    length=len(sequence),
                )
            )

        Protein.objects.bulk_create(objects)

        return len(objects)
    