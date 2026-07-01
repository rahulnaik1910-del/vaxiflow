from proteins.models import Protein

from signalp.models import SignalPResult


class SignalPImporter:
    """
    Imports parsed SignalP predictions
    into the database.
    """

    @staticmethod
    def import_results(predictions):
        """
        Parameters
        ----------
        predictions : list[dict]

        Returns
        -------
        int
            Number of imported predictions.
        """

        imported = 0

        for prediction in predictions:

            protein_id = prediction.get("protein_id")

            if not protein_id:
                continue

            try:

                protein = Protein.objects.get(
                    protein_id=protein_id
                )

            except Protein.DoesNotExist:

                continue

            SignalPResult.objects.update_or_create(

                protein=protein,

                defaults={

                    "prediction": prediction.get(
                        "prediction",
                        "",
                    ),

                    "probability": prediction.get(
                        "probability",
                        0.0,
                    ),

                    "cleavage_site": prediction.get(
                        "cleavage_site",
                        "",
                    ),

                    "version": prediction.get(
                        "version",
                        "SignalP",
                    ),

                },

            )

            imported += 1

        return imported
    