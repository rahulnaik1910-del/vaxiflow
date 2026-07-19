from pathlib import Path

from pipeline.services.importers.bakta_importer import BaktaImporter

gff3 = Path("media/bakta_light_test_ecoli/ecoli_annotation.gff3")
faa = Path("media/bakta_light_test_ecoli/ecoli_annotation.faa")

proteins = BaktaImporter(gff3, faa).parse()

print("=" * 60)
print("Bakta Importer Test")
print("=" * 60)
print(f"Total proteins: {len(proteins)}")
print()

print("First protein:")
print()
print(proteins[0])
