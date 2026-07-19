from pathlib import Path


class GFF3Parser:
    def __init__(self, gff3_file):
        self.gff3_file = Path(gff3_file)

    @staticmethod
    def parse_attributes(attributes):
        result = {}

        for item in attributes.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                result[key] = value

        return result

    def parse(self):
        proteins = []

        with open(self.gff3_file, "r", encoding="utf-8") as f:

            for line in f:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                parts = line.split("\t")

                if len(parts) != 9:
                    continue

                feature = parts[2]

                if feature != "CDS":
                    continue

                start = int(parts[3])
                end = int(parts[4])
                strand = parts[6]

                attribute_dict = self.parse_attributes(parts[8])

                proteins.append(
                    {
                        "protein_id": attribute_dict.get("ID"),
                        "gene": attribute_dict.get("gene"),
                        "product": attribute_dict.get("product"),
                        "locus_tag": attribute_dict.get("locus_tag"),
                        "start": start,
                        "end": end,
                        "strand": strand,
                    }
                )

        return proteins
    