from pathlib import Path

from pipeline.services.parsers.faa_parser import FAAParser

faa_file = Path("media/bakta_light_test_ecoli/ecoli_annotation.faa")

parser = FAAParser(faa_file)
proteins = parser.parse()

print("=" * 50)
print("FAA Parser Test")
print("=" * 50)
print(f"Total proteins: {len(proteins)}")
print()

print("First 5 proteins:")
print()

for protein in proteins[:5]:
    print(protein)
    