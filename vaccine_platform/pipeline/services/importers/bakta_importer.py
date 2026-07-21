from pathlib import Path

from proteins.models import Protein

from pipeline.services.parsers.faa_parser import FAAParser
from pipeline.services.parsers.gff3_parser import GFF3Parser


class BaktaImporter:
    """
    Reads the .faa and .gff3 files Bakta wrote for a single genome
    and imports the resulting proteins into the database, linked to
    the given Analysis record.
    """

    @staticmethod
    def import_from_output(genome, analysis, output_dir, prefix):
        """
        genome:     users.models.Genome
        analysis:   users.models.Analysis  (analysis_type="bakta")
        output_dir: str or Path - directory Bakta wrote its output to
        prefix:     str - the --prefix passed to Bakta, e.g.
                    "genome_{id}_annotation"

        Returns a dict:
            {
                "imported": <int>,
                "skipped": <int>,
                "log": <str>,
            }
        """

        output_dir = Path(output_dir)

        faa_file = output_dir / f"{prefix}.faa"
        gff3_file = output_dir / f"{prefix}.gff3"

        log_lines = [
            f"Looking for Bakta output in: {output_dir}",
            f"FAA file: {faa_file} (exists={faa_file.exists()})",
            f"GFF3 file: {gff3_file} (exists={gff3_file.exists()})",
        ]

        if not faa_file.exists():
            log_lines.append(
                "No .faa file found - nothing to import."
            )
            return {
                "imported": 0,
                "skipped": 0,
                "log": "\n".join(log_lines),
            }

        proteins_from_faa = FAAParser(faa_file).parse()
        features_from_gff3 = GFF3Parser(gff3_file).parse()

        log_lines.append(
            f"Parsed {len(proteins_from_faa)} sequences from FAA."
        )
        log_lines.append(
            f"Parsed {len(features_from_gff3)} CDS features from GFF3."
        )

        protein_objects = []
        skipped = 0

        for entry in proteins_from_faa:

            protein_id = entry["protein_id"]
            sequence = entry["sequence"]

            if not sequence:
                skipped += 1
                continue

            gff3_feature = features_from_gff3.get(protein_id, {})

            # Prefer the GFF3 product (more structured) but fall back
            # to whatever followed the ID on the FASTA header line.
            product = (
                gff3_feature.get("product")
                or entry.get("product", "")
            )

            gene = gff3_feature.get("gene", "")

            protein_objects.append(
                Protein(
                    analysis=analysis,
                    protein_id=protein_id,
                    gene=gene,
                    product=product,
                    sequence=sequence,
                    length=len(sequence),
                )
            )

        created = Protein.objects.bulk_create(protein_objects)

        log_lines.append(
            f"Imported {len(created)} proteins into the database "
            f"(skipped {skipped} empty/invalid entries)."
        )

        return {
            "imported": len(created),
            "skipped": skipped,
            "log": "\n".join(log_lines),
        }
