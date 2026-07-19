from pathlib import Path

from pipeline.services.parsers.gff3_parser import GFF3Parser


gff3_file = Path("media/bakta_light_test_ecoli/ecoli_annotation.gff3")

parser = GFF3Parser(gff3_file)

proteins = parser.parse()

print("=" * 50)
print("Parser Test")
print("=" * 50)
print(f"Total proteins found: {len(proteins)}")
print()

print("First 5 proteins:")
print()

for protein in proteins[:5]:
    print(protein)
    