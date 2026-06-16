#!/usr/bin/env python3
"""Download the Graz order type database files.

By default downloads n=3..9 (otypes + property files).
Use --also10 to also download the large n=10 otypes file (~3 GB uncompressed).

Usage:
    python3 download.py
    python3 download.py --also10

Files are saved to otypes/ and properties/ next to this script.
"""

import argparse
import sys
import urllib.request
from pathlib import Path

BASE = "http://www.ist.tugraz.at/staff/aichholzer/research/rp/triangulations/ordertypes/data"

# property files — exact filenames as listed on the server
# (extensions vary per file/n; sourced from the download page)
PROPERTY_FILES = [
    # name       n=3      n=4      n=5      n=6      n=7      n=8      n=9
    ("crossn", ["b08",   "b08",   "b08",   "b08",   "b08",   "b08",   "b08"]),
    ("extrem", ["b08",   "b08",   "b08",   "b08",   "b08",   "b08",   "b08"]),
    ("kgons",  ["b08",   "b08",   "b08",   "b08",   "b08",   "b08",   "b08"]),
    ("ekgons", ["b08",   "b08",   "b08",   "b08",   "b08",   "b08",   "b08"]),
    ("crossf", ["b08",   "b08",   "b08",   "b08",   "b08",   "b08",   "b08"]),
    ("trinum", ["b08",   "b08",   "b08",   "b08",   "b08",   "b08",   "b16"]),
]

ROOT = Path(__file__).parent

# OT counts per n (for progress display)
OT_COUNTS = {3: 1, 4: 2, 5: 3, 6: 16, 7: 135, 8: 3315, 9: 158_817, 10: 14_309_547}


def _progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 // total_size)
        bar = "#" * (pct // 5) + "." * (20 - pct // 5)
        print(f"\r    [{bar}] {pct:3d}%  {downloaded:>12,} / {total_size:,} bytes",
              end="", flush=True)
    else:
        print(f"\r    {downloaded:>12,} bytes", end="", flush=True)


def download(url: str, dest: Path, expected_size: int | None = None) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        # verify it's not a stale HTML error page (they are all exactly 6,653 bytes)
        with open(dest, "rb") as f:
            head = f.read(64).lstrip(b"\xef\xbb\xbf").lower()
        if (head.startswith(b"<!doctype html") or head.startswith(b"<html")
                or head.startswith(b"<?xml")):
            print(f"  stale {dest.name} (HTML error page, re-downloading)")
            dest.unlink()
        else:
            print(f"  skip  {dest.name} (already present, {dest.stat().st_size:,} bytes)")
            return True

    if expected_size:
        print(f"  fetch {dest.name}  (~{expected_size:,} bytes expected)")
    else:
        print(f"  fetch {dest.name}")
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [("User-Agent", "wget/1.21")]
        with opener.open(url) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            block = 8192
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(block)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    _progress(downloaded // block, block, total)
        _progress(1, downloaded, downloaded)  # force 100%
        print()  # newline after progress bar
        size = dest.stat().st_size
        # detect HTML error page (case-insensitive, handles BOM)
        with open(dest, "rb") as f:
            head = f.read(64).lstrip(b"\xef\xbb\xbf").lower()
        if (head.startswith(b"<!doctype html") or head.startswith(b"<html")
                or head.startswith(b"<?xml")):
            print(f"    ERROR: server returned an HTML error page — file not available")
            dest.unlink()
            return False
        print(f"    OK  {size:,} bytes")
        return True
    except Exception as e:
        print(f"\n    FAILED: {e}")
        dest.unlink(missing_ok=True)
        return False


LICENSE_NOTICE = """\
================================================================================
  Graz Order Type Database — License Terms
================================================================================

  Usage of the data base is free for non-commercial, non-governmental
  and non-military purposes.

  See: http://www.ist.tugraz.at/staff/aichholzer/research/rp/triangulations/ordertypes/readme.txt
================================================================================
"""


def confirm_license() -> bool:
    """Display the OTDB license terms and require explicit 'yes' confirmation."""
    print(LICENSE_NOTICE)
    try:
        answer = input("Do you accept these terms? Type 'yes' to proceed: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer.lower() == "yes"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--also10", action="store_true",
                        help="also download the large n=10 otypes file")
    parser.add_argument("--properties", action="store_true",
                        help="also download property files (crossn, extrem, kgons, ekgons, crossf)")
    parser.add_argument("--accept-license", action="store_true",
                        help="accept the OTDB license terms non-interactively")
    args = parser.parse_args()

    if not args.accept_license:
        if not confirm_license():
            print("Download aborted.")
            sys.exit(1)

    n_max_otypes = 10 if args.also10 else 9
    n_max_props  = 9  # no property files for n=10 on server

    errors = 0

    # otypes files: each OT is stored as n*(n-1)/2 bytes (b08) or n*(n-1) bytes (b16)
    print("-- otypes --")
    for n in range(3, n_max_otypes + 1):
        nn = f"{n:02d}"
        ext = "b08" if n <= 8 else "b16"
        bytes_per_ot = n * (n - 1) // 2 if n <= 8 else n * (n - 1)
        expected = OT_COUNTS.get(n, 0) * bytes_per_ot
        ok = download(f"{BASE}/otypes{nn}.{ext}",
                      ROOT / "otypes" / f"otypes{nn}.{ext}",
                      expected_size=expected)
        if not ok:
            errors += 1

    # property files n=3..9
    if args.properties:
        print("\n-- properties --")
        for name, exts in PROPERTY_FILES:
            for i, n in enumerate(range(3, n_max_props + 1)):
                nn = f"{n:02d}"
                ext = exts[i]
                ok = download(f"{BASE}/{name}{nn}.{ext}",
                              ROOT / "properties" / f"{name}{nn}.{ext}")
                if not ok:
                    errors += 1

    print()
    if errors:
        print(f"WARNING: {errors} file(s) failed to download.")
        sys.exit(1)
    else:
        print("All files downloaded successfully.")


if __name__ == "__main__":
    main()
