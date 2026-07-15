from pathlib import Path


ALLOWED_GENOME_EXTENSIONS = {
    ".fasta",
    ".fa",
    ".fna",
}


ALLOWED_NUCLEOTIDES = set(
    "ACGTUNRYSWKMBDHVacgtunryswkmbdhv"
)


def validate_nucleotide_fasta(file_path):
    """
    Validate that a file is a nucleotide FASTA genome file.

    Returns:
        tuple:
            (True, message) if valid.
            (False, message) if invalid.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        return (
            False,
            f"Genome file does not exist: {file_path}",
        )

    if not file_path.is_file():
        return (
            False,
            f"Genome path is not a file: {file_path}",
        )

    extension = file_path.suffix.lower()

    if extension not in ALLOWED_GENOME_EXTENSIONS:
        return (
            False,
            "Only nucleotide FASTA files "
            "(.fasta, .fa, .fna) are allowed.",
        )

    header_found = False
    sequence_found = False

    try:

        with file_path.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as handle:

            for line in handle:

                line = line.strip()

                if not line:
                    continue

                if line.startswith(">"):
                    header_found = True
                    continue

                sequence_found = True

                invalid_characters = (
                    set(line)
                    - ALLOWED_NUCLEOTIDES
                )

                if invalid_characters:

                    invalid_preview = "".join(
                        sorted(
                            invalid_characters
                        )
                    )[:20]

                    return (
                        False,
                        "The uploaded file is not a valid "
                        "nucleotide genome FASTA. "
                        "Invalid sequence characters detected: "
                        f"{invalid_preview}",
                    )

    except OSError as exc:

        return (
            False,
            f"Could not read genome file: {exc}",
        )

    if not header_found:

        return (
            False,
            "Invalid FASTA file: no header "
            "starting with '>' was found.",
        )

    if not sequence_found:

        return (
            False,
            "Invalid FASTA file: no nucleotide "
            "sequence was found.",
        )

    return (
        True,
        "Valid nucleotide genome FASTA.",
    )
