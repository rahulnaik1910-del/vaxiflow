import glob
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

# Version flags confirmed by actually running each tool where
# installed (blastp, makeblastdb, panaroo, psort - checked directly
# during development). Bakta's is the standard argparse convention
# but hasn't been directly confirmed the same way, since Bakta isn't
# installed in the environment this command was developed in - if
# it turns out wrong, this just falls back to "version unknown"
# rather than breaking the whole check.
# ToxinPred2 and Phobius have no known --version flag (confirmed
# toxinpred2 lacks one - it errors asking for required -i; Phobius
# is a legacy Perl script with no such option) - version check is
# skipped for those two by design, not a bug.
VERSION_FLAGS = {
    "bakta": "--version",
    "panaroo": "--version",
    "blastp": "-version",
    "makeblastdb": "-version",
    "psort": "--version",
}


class Command(BaseCommand):

    help = (
        "Checks whether every external tool and reference database "
        "the pipeline needs is actually available on this machine, "
        "and prints a clear pass/fail/optional report plus an "
        "overall readiness verdict."
    )

    def handle(self, *args, **options):

        results = []

        results.append(
            self._check_executable(
                "Bakta",
                settings.BAKTA_EXECUTABLE,
                required=True,
                version_key="bakta",
            )
        )
        results.append(
            self._check_path_exists(
                "Bakta database",
                settings.BAKTA_DB,
                required=True,
            )
        )

        results.append(
            self._check_executable(
                "Panaroo",
                settings.PANAROO_EXECUTABLE,
                required=True,
                version_key="panaroo",
            )
        )

        results.append(
            self._check_executable(
                "blastp",
                "blastp",
                required=True,
                version_key="blastp",
            )
        )
        results.append(
            self._check_executable(
                "makeblastdb",
                "makeblastdb",
                required=False,
                version_key="makeblastdb",
            )
        )

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

        human_db = settings.BLAST_DATABASES.get("human_swissprot")
        results.append(
            self._check_blast_db(
                "Human proteome database",
                str(human_db) if human_db else "",
                required=True,
            )
        )

        results.append(
            self._check_executable(
                "PSORTb (psort)",
                settings.PSORTB_EXECUTABLE,
                required=True,
                version_key="psort",
            )
        )

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

        results.append(
            self._check_executable(
                "ToxinPred2",
                settings.TOXINPRED2_EXECUTABLE,
                required=True,
            )
        )

        results.append(self._check_iedb())

        self._print_report(results)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _get_version(self, resolved_path, version_key):

        flag = VERSION_FLAGS.get(version_key)

        if not flag:
            return None

        try:

            result = subprocess.run(
                [resolved_path, flag],
                capture_output=True,
                text=True,
                timeout=15,
            )

            output = (result.stdout or result.stderr).strip()

            if not output:
                return None

            # Keep just the first line - version banners can be
            # multi-line (blastp/makeblastdb print two lines).
            return output.splitlines()[0][:80]

        except Exception:
            return None

    def _check_executable(
        self, name, path, required, note=None, version_key=None
    ):

        if not path:
            return {
                "name": name,
                "status": (
                    "MISSING-REQUIRED"
                    if required
                    else "MISSING-OPTIONAL"
                ),
                "detail": "not configured",
                "note": note,
                "version": None,
            }

        resolved = shutil.which(path) or (
            path
            if Path(path).is_file()
            and Path(path).stat().st_mode & 0o111
            else None
        )

        if not resolved:
            return {
                "name": name,
                "status": (
                    "MISSING-REQUIRED"
                    if required
                    else "MISSING-OPTIONAL"
                ),
                "detail": f"not found at configured path: {path}",
                "note": note,
                "version": None,
            }

        version = (
            self._get_version(resolved, version_key)
            if version_key
            else None
        )

        return {
            "name": name,
            "status": "OK",
            "detail": f"found at {resolved}",
            "note": note,
            "version": version,
        }

    def _check_path_exists(self, name, path, required, note=None):

        if not path or not Path(path).exists():

            return {
                "name": name,
                "status": (
                    "MISSING-REQUIRED"
                    if required
                    else "MISSING-OPTIONAL"
                ),
                "detail": f"not found at: {path}",
                "note": note,
                "version": None,
            }

        return {
            "name": name,
            "status": "OK",
            "detail": f"found at {path}",
            "note": note,
            "version": None,
        }

    def _check_blast_db(self, name, db_prefix, required, note=None):

        if not db_prefix:

            return {
                "name": name,
                "status": (
                    "MISSING-REQUIRED"
                    if required
                    else "MISSING-OPTIONAL"
                ),
                "detail": "not configured",
                "note": note,
                "version": None,
            }

        matches = glob.glob(f"{db_prefix}.*")

        if matches:
            return {
                "name": name,
                "status": "OK",
                "detail": (
                    f"found ({len(matches)} files at prefix "
                    f"{db_prefix})"
                ),
                "note": note,
                "version": None,
            }

        return {
            "name": name,
            "status": (
                "MISSING-REQUIRED" if required else "MISSING-OPTIONAL"
            ),
            "detail": f"no files found at prefix: {db_prefix}",
            "note": note,
            "version": None,
        }

    def _check_iedb(self):

        try:

            import requests

            response = requests.get(
                settings.IEDB_API_BASE_URL,
                timeout=10,
            )

            return {
                "name": "IEDB API connectivity",
                "status": "OK",
                "detail": f"reachable (HTTP {response.status_code})",
                "note": None,
                "version": None,
            }

        except Exception as error:

            return {
                "name": "IEDB API connectivity",
                "status": "MISSING-REQUIRED",
                "detail": f"unreachable: {error}",
                "note": (
                    "Check internet access from this machine to "
                    "tools-cluster-interface.iedb.org"
                ),
                "version": None,
            }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _print_report(self, results):

        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write("VAXIFLOW TOOL & DATABASE AVAILABILITY REPORT")
        self.stdout.write("=" * 70)

        for r in results:

            if r["status"] == "OK":
                marker = self.style.SUCCESS("[  OK  ]")
            elif r["status"] == "MISSING-OPTIONAL":
                marker = self.style.WARNING("[ SKIP ]")
            else:
                marker = self.style.ERROR("[ FAIL ]")

            line = f"{marker} {r['name']}: {r['detail']}"

            if r["version"]:
                line += f"  ({r['version']})"

            self.stdout.write(line)

            if r["note"]:
                self.stdout.write(f"         -> {r['note']}")

        self.stdout.write("=" * 70)

        required_failures = [
            r for r in results if r["status"] == "MISSING-REQUIRED"
        ]
        optional_skips = [
            r for r in results if r["status"] == "MISSING-OPTIONAL"
        ]

        if required_failures:

            verdict = "NOT READY"
            style = self.style.ERROR

        elif optional_skips:

            verdict = "READY WITH SKIPS"
            style = self.style.WARNING

        else:

            verdict = "READY TO RUN"
            style = self.style.SUCCESS

        self.stdout.write("")
        self.stdout.write(style(f"OVERALL STATUS: {verdict}"))
        self.stdout.write("")

        if required_failures:
            self.stdout.write(
                self.style.ERROR(
                    f"{len(required_failures)} required tool(s) "
                    "missing - these WILL block the pipeline:"
                )
            )
            for r in required_failures:
                self.stdout.write(f"  - {r['name']}")

        if optional_skips:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(optional_skips)} optional item(s) will "
                    "cause their stage to be skipped (not failed):"
                )
            )
            for r in optional_skips:
                self.stdout.write(f"  - {r['name']}")
