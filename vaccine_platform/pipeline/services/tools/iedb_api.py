import re

import requests
from django.conf import settings

# NOTE: This client's request payloads and response parsing are
# based on the real, documented IEDB Tools API contract - confirmed
# directly from the source of the `iedb` PyPI package (a thin,
# actively-referenced wrapper around this same API), not guessed
# from memory. However, tools-cluster-interface.iedb.org is not
# reachable from this development sandbox's network, so none of
# this has been exercised against a live response in this
# environment - only the response *parsing* has been tested, against
# hand-built text matching this confirmed format. Verify against a
# real API call before trusting results in production.


class IedbApiError(Exception):
    pass


class IedbApiClient:

    @staticmethod
    def _parse_tabular_response(text, expected_first_column):
        """
        IEDB's tools API returns a tab-delimited table as plain
        text: first line is column headers, each subsequent line is
        a row. Returns a list of dicts.

        expected_first_column: the column name the response should
        start with if the call succeeded (e.g. "allele" for MHC-I/
        II, "Position" for B-cell) - if the response doesn't start
        with this, IEDB returned an error message instead of a
        table, and we raise with that message.
        """

        if not text or not text.strip():
            raise IedbApiError("Empty response from IEDB API.")

        if not text.startswith(expected_first_column):
            raise IedbApiError(
                f"IEDB API returned an error: {text.strip()}"
            )

        lines = [
            line
            for line in re.split(r"\n+", text.strip())
            if line
        ]

        headers = re.split(r"\t+", lines[0])

        rows = []

        for line in lines[1:]:

            values = re.split(r"\t+", line)

            rows.append(dict(zip(headers, values)))

        return rows

    @staticmethod
    def query_bcell_epitope(sequence, method=None):
        """
        sequence: str - protein amino acid sequence.
        method:   str - defaults to settings.IEDB_BCELL_METHOD.

        Returns a list of dicts, one per residue, with keys
        typically including "Position", "Residue", "Score",
        "Assignment" (Bepipred-2.0's per-residue output columns).
        """

        method = method or settings.IEDB_BCELL_METHOD

        response = requests.post(
            url=f"{settings.IEDB_API_BASE_URL}/bcell/",
            data={
                "method": method,
                "sequence_text": sequence,
                # Required by the API for other B-cell methods; not
                # used by Bepipred-2.0 itself, but the field must be
                # present.
                "window_size": 9,
            },
            timeout=settings.IEDB_REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return IedbApiClient._parse_tabular_response(
            response.text, "Position"
        )

    @staticmethod
    def query_mhci_binding(
        sequence, alleles, lengths, method=None
    ):
        """
        sequence: str - protein amino acid sequence.
        alleles:  list of str, e.g. ["HLA-A*02:01", ...]
        lengths:  list of int, e.g. [9]
        method:   str - defaults to settings.IEDB_MHCI_METHOD.

        Returns a list of dicts, one per predicted peptide/allele/
        length combination, with keys typically including "allele",
        "start", "end", "length", "peptide", "ic50",
        "percentile_rank" (exact column set can vary by method).
        """

        method = method or settings.IEDB_MHCI_METHOD

        response = requests.post(
            url=f"{settings.IEDB_API_BASE_URL}/mhci/",
            data={
                "method": method,
                "sequence_text": sequence,
                "allele": ",".join(alleles),
                "length": ",".join(str(x) for x in lengths),
            },
            timeout=settings.IEDB_REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return IedbApiClient._parse_tabular_response(
            response.text, "allele"
        )

    @staticmethod
    def query_mhcii_binding(sequence, alleles, method=None):
        """
        sequence: str - protein amino acid sequence.
        alleles:  list of str, e.g. ["HLA-DRB1*01:01", ...]
        method:   str - defaults to settings.IEDB_MHCII_METHOD.

        MHC-II peptide length is fixed at 15 by the IEDB API's own
        convention for this tool, so no length parameter is exposed
        here (unlike MHC-I).

        Returns a list of dicts, one per predicted peptide/allele
        combination.
        """

        method = method or settings.IEDB_MHCII_METHOD

        response = requests.post(
            url=f"{settings.IEDB_API_BASE_URL}/mhcii/",
            data={
                "method": method,
                "sequence_text": sequence,
                "allele": ",".join(alleles),
                "length": 15,
            },
            timeout=settings.IEDB_REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return IedbApiClient._parse_tabular_response(
            response.text, "allele"
        )
