from pathlib import Path

from django.conf import settings

from pipeline.models import AllergenicityResult
from pipeline.services.parsers.allergen_parser import AllergenParser


class AllergenicityImporter:

    @staticmethod
    def build_kmer_set(fasta_file, k=None):
        """
        Reads every sequence in the allergen reference FASTA and
        returns the set of all contiguous k-mers across all of them,
        for the FAO/WHO exact-match criterion.

        fasta_file: str/Path - the allergen database's source FASTA
                    (settings.ALLERGEN_DATABASE_FASTA)
        k:          int - k-mer length, defaults to
                    settings.ALLERGEN_EXACT_MATCH_LENGTH
        """

        if k is None:
            k = settings.ALLERGEN_EXACT_MATCH_LENGTH

        fasta_file = Path(fasta_file)

        kmers = set()

        if not fasta_file.exists():
            return kmers

        sequence_lines = []

        def flush():
            sequence = "".join(sequence_lines).upper()
            for i in range(0, len(sequence) - k + 1):
                kmers.add(sequence[i:i + k])

        with open(fasta_file, "r") as handle:

            for raw_line in handle:

                line = raw_line.strip()

                if not line:
                    continue

                if line.startswith(">"):
                    flush()
                    sequence_lines = []
                else:
                    sequence_lines.append(line)

        flush()

        return kmers

    @staticmethod
    def has_exact_match(sequence, kmer_set, k=None):
        """
        True if any k-mer of `sequence` appears in `kmer_set`.
        """

        if k is None:
            k = settings.ALLERGEN_EXACT_MATCH_LENGTH

        sequence = sequence.upper()

        if not kmer_set:
            return False

        for i in range(0, len(sequence) - k + 1):

            if sequence[i:i + k] in kmer_set:
                return True

        return False

    @staticmethod
    def import_results(proteins, output_file, kmer_set):
        """
        proteins:    list of Protein instances that were screened.
        output_file: str/Path - the allergen_hits.tsv file written
                     by AllergenExecutor
        kmer_set:    set of str - from build_kmer_set(), used for
                     the exact-match criterion

        Returns a dict:
            {
                "screened": <int>,
                "allergens": <int>,
                "not_allergens": <int>,
                "log": <str>,
            }
        """

        hits = AllergenParser(output_file).parse()

        log_lines = [
            f"Parsed {len(hits)} raw BLAST hits from {output_file}.",
            f"Screening {len(proteins)} candidate proteins.",
            "FAO/WHO criteria: identity >= "
            f"{settings.ALLERGEN_MIN_IDENTITY}% over an alignment "
            f">= {settings.ALLERGEN_MIN_ALIGNMENT_LENGTH}aa, OR an "
            f"exact {settings.ALLERGEN_EXACT_MATCH_LENGTH}-mer "
            "match.",
            f"Allergen reference k-mer set size: {len(kmer_set)}",
        ]

        allergen_count = 0
        not_allergen_count = 0

        for protein in proteins:

            hit = hits.get(protein.protein_id)

            has_sliding_window_hit = False

            if hit is not None:

                has_sliding_window_hit = (
                    hit["identity"] >= settings.ALLERGEN_MIN_IDENTITY
                    and hit["alignment_length"]
                    >= settings.ALLERGEN_MIN_ALIGNMENT_LENGTH
                )

            has_exact_match = (
                AllergenicityImporter.has_exact_match(
                    protein.sequence, kmer_set
                )
            )

            is_allergen = (
                has_sliding_window_hit or has_exact_match
            )

            AllergenicityResult.objects.update_or_create(
                protein=protein,
                defaults={
                    "best_subject_id": (
                        hit["subject_id"] if hit else ""
                    ),
                    "identity": hit["identity"] if hit else None,
                    "alignment_length": (
                        hit["alignment_length"] if hit else None
                    ),
                    "evalue": hit["evalue"] if hit else None,
                    "bit_score": hit["bit_score"] if hit else None,
                    "has_sliding_window_hit": (
                        has_sliding_window_hit
                    ),
                    "has_exact_match": has_exact_match,
                    "is_allergen": is_allergen,
                },
            )

            if is_allergen:
                allergen_count += 1
            else:
                not_allergen_count += 1

        log_lines.append(
            f"Result: {allergen_count} flagged as allergens, "
            f"{not_allergen_count} not flagged."
        )

        return {
            "screened": len(proteins),
            "allergens": allergen_count,
            "not_allergens": not_allergen_count,
            "log": "\n".join(log_lines),
        }
