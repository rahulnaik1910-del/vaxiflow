import glob
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = (
        "Checks whether every external tool and reference database "
        "the pipeline needs is actually available on this machine, "
        "and prints a clear pass/fail/optional report."
    )

    def handle(self, *args, **options):

        results = []

        # --- Bakta ---
        results.append(
            self._check_executable(
                "Bakta",
                settings.BAKTA_EXECUTABLE,
                required=True,
            )
        )
        results.append(
            self._check_path_exists(
                "Bakta database",
                settings.BAKTA_DB,
                required=True,
            )
        )

        # --- Panaroo ---
        results.append(
            self._check_executable(
                "Panaroo",
                settings.PANAROO_EXECUTABLE,
                required=True,
            )
        )

        # --- BLAST+ (shared by DEG, Human Homology, Allergenicity) ---
        results.append(
            self._check_executable(
                "blastp",
                "blastp",
                required=True,
            )
        )
        results.append(
            self._check_executable(
                "makeblastdb",
                "makeblastdb",
                required=False,
            )
        )

        # --- DEG database ---
        results.append(
            self._check_blast_db(
                "DEG database",
                settings.DEG_DATABASE,
                required=False,
                note=(
                    "DEG stage will be SKIPPED (not failed) if "
                    "missing - see setup checklist to configure."
                ),
            )
        )

        # --- Human proteome (Human Homology stage) ---
        human_db = settings.BLAST_DATABASES.get(
            "human_swissprot"
        )
        results.append(
            self._check_blast_db(
                "Human proteome database",
                str(human_db) if human_db else "",
                required=True,
            )
        )

        # --- PSORTb ---
        results.append(
            self._check_executable(
                "PSORTb (psort)",
                settings.PSORTB_EXECUTABLE,
                required=True,
            )
        )

        # --- Phobius (optional) ---
        results.append(
            self._check_executable(
                "Phobius",
                settings.PHOBIUS_EXECUTABLE,
                required=False,
                note=(
                    "Optional - native Kyte-Doolittle fallback is "
                    "used automatically if missing."
                ),
            )
        )

        # --- Allergen database ---
        results.append(
            self._check_blast_db(
                "Allergen database",
                settings.ALLERGEN_DATABASE,
                required=False,
                note=(
                    "Allergenicity stage will be SKIPPED (not "
                    "failed) if missing - see setup checklist."
                ),
            )
        )

        # --- ToxinPred2 ---
        results.append(
            self._check_executable(
                "ToxinPred2",
                settings.TOXINPRED2_EXECUTABLE,
                required=True,
            )
        )

        # --- IEDB API connectivity ---
        results.append(self._check_iedb())

        # --- Print report ---
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write("VAXIFLOW TOOL & DATABASE AVAILABILITY REPORT")
        self.stdout.write("=" * 70)

        for name, status, detail, note in results:

            if status == "OK":
                marker = self.style.SUCCESS("[  OK  ]")
            elif status == "MISSING-OPTIONAL":
                marker = self.style.WARNING("[ SKIP ]")
            else:
                marker = self.style.ERROR("[ FAIL ]")

            self.stdout.write(f"{marker} {name}: {detail}")

            if note:
                self.stdout.write(f"         -> {note}")

        self.stdout.write("=" * 70)

        required_failures = [
            r for r in results if r[1] == "MISSING-REQUIRED"
        ]

        if required_failures:
            self.stdout.write(
                self.style.ERROR(
                    f"\n{len(required_failures)} required tool(s) "
                    "missing - these WILL block the pipeline."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nAll required tools are available. Optional/"
                    "skippable items are noted above."
                )
            )

    def _check_executable(self, name, path, required, note=None):

        if not path:
            return (
                name,
                "MISSING-REQUIRED" if required else (
                    "MISSING-OPTIONAL"
                ),
                "not configured",
                note,
            )

        resolved = shutil.which(path) or (
            path
            if Path(path).is_file()
            and Path(path).stat().st_mode & 0o111
            else None
        )

        if resolved:
            return (name, "OK", f"found at {resolved}", note)

        return (
            name,
            "MISSING-REQUIRED" if required else "MISSING-OPTIONAL",
            f"not found at configured path: {path}",
            note,
        )

    def _check_path_exists(self, name, path, required, note=None):

        if not path or not Path(path).exists():

            return (
                name,
                "MISSING-REQUIRED" if required else (
                    "MISSING-OPTIONAL"
                ),
                f"not found at: {path}",
                note,
            )

        return (name, "OK", f"found at {path}", note)

    def _check_blast_db(self, name, db_prefix, required, note=None):

        if not db_prefix:

            return (
                name,
                "MISSING-REQUIRED" if required else (
                    "MISSING-OPTIONAL"
                ),
                "not configured",
                note,
            )

        matches = glob.glob(f"{db_prefix}.*")

        if matches:
            return (
                name,
                "OK",
                f"found ({len(matches)} files at prefix {db_prefix})",
                note,
            )

        return (
            name,
            "MISSING-REQUIRED" if required else "MISSING-OPTIONAL",
            f"no files found at prefix: {db_prefix}",
            note,
        )

    def _check_iedb(self):

        try:

            import requests

            response = requests.get(
                settings.IEDB_API_BASE_URL,
                timeout=10,
            )

            return (
                "IEDB API connectivity",
                "OK",
                f"reachable (HTTP {response.status_code})",
                None,
            )

        except Exception as error:

            return (
                "IEDB API connectivity",
                "MISSING-REQUIRED",
                f"unreachable: {error}",
                (
                    "Check internet access from this machine to "
                    "tools-cluster-interface.iedb.org"
                ),
            )
