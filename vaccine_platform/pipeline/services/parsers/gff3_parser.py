from pathlib import Path


class GFF3Parser:
    """
    Parses a Bakta .gff3 annotation file.

    Standard GFF3 feature line (tab-separated, 9 columns):

        seqid  source  type  start  end  score  strand  phase  attributes

    The attributes column is a ';'-separated list of key=value pairs,
    e.g. "ID=genome_1_annotation_00001;Name=dnaA;gene=dnaA;
    product=Chromosomal replication initiator protein DnaA;locus_tag=..."

    We only care about CDS features, since those correspond to the
    proteins Bakta also writes to the .faa file.
    """

    def __init__(self, gff3_file):
        self.gff3_file = Path(gff3_file)

    def parse(self):
        """
        Read the GFF3 file and return a dict keyed by feature ID:
            {
                "genome_1_annotation_00001": {
                    "gene": "dnaA",
                    "locus_tag": "...",
                    "product": "...",
                },
                ...
            }
        """
        features = {}

        if not self.gff3_file.exists():
            return features

        with open(self.gff3_file, "r") as handle:

            for raw_line in handle:

                line = raw_line.rstrip("\n").rstrip("\r")

                if not line or line.startswith("#"):
                    continue

                if line.startswith(">"):
                    # Reached an embedded FASTA section, if present.
                    break

                columns = line.split("\t")

                if len(columns) < 9:
                    continue

                feature_type = columns[2]

                if feature_type != "CDS":
                    continue

                attributes = self._parse_attributes(columns[8])

                feature_id = attributes.get("ID")

                if not feature_id:
                    continue

                features[feature_id] = {
                    "gene": attributes.get(
                        "gene", attributes.get("Name", "")
                    ),
                    "locus_tag": attributes.get("locus_tag", ""),
                    "product": attributes.get("product", ""),
                }

        return features

    @staticmethod
    def _parse_attributes(attribute_string):

        attributes = {}

        for pair in attribute_string.split(";"):

            pair = pair.strip()

            if not pair or "=" not in pair:
                continue

            key, value = pair.split("=", 1)

            attributes[key.strip()] = value.strip()

        return attributes
