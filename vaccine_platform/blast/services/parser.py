from Bio.Blast import NCBIXML


class BlastParser:
    """
    Parses BLAST XML output.
    """

    @staticmethod
    def parse(xml_file):

        results = []

        with open(xml_file) as handle:

            blast_records = NCBIXML.parse(handle)

            for record in blast_records:

                for alignment in record.alignments:

                    for hsp in alignment.hsps:

                        identity = (
                            hsp.identities
                            / hsp.align_length
                        ) * 100

                        results.append(

                            {
                                "subject_id": alignment.hit_id,
                                "subject_title": alignment.hit_def,
                                "identity": identity,
                                "alignment_length": hsp.align_length,
                                "evalue": hsp.expect,
                                "bit_score": hsp.bits,
                            }

                        )

        return results
    