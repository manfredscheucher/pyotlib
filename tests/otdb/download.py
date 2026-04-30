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

BASE = "http://www.ist.tugraz.at/staff/aichholzer/research/rp/triangulations/ordertypes"

# property files: 1 byte per OT for n<=8, 2 bytes for n=9
# (n=10 has no property files on the server)
PROPERTY_FILES = [
    "crossn",   # rectilinear crossing number
    "extrem",   # number of extreme (hull) points
    "kgons",    # convex k-gons (n-2 bytes per OT: k=3..n)
    "ekgons",   # empty convex k-gons (n-2 bytes per OT: k=3..n)
    "crossf",   # max crossing family size
]

ROOT = Path(__file__).parent


def download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip  {dest.name} (already present)")
        return True
    print(f"  fetch {dest.name} ...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        size = dest.stat().st_size
        print(f"{size:,} bytes")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        dest.unlink(missing_ok=True)
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--also10", action="store_true",
                        help="also download the large n=10 otypes file")
    args = parser.parse_args()

    n_max_otypes = 10 if args.also10 else 9
    n_max_props  = 9  # no property files for n=10 on server

    errors = 0

    # otypes files
    print("-- otypes --")
    for n in range(3, n_max_otypes + 1):
        nn = f"{n:02d}"
        ext = "b08" if n <= 8 else "b16"
        ok = download(f"{BASE}/otypes{nn}.{ext}", ROOT / "otypes" / f"otypes{nn}.{ext}")
        if not ok:
            errors += 1

    # property files n=3..9
    print("\n-- properties --")
    for name in PROPERTY_FILES:
        for n in range(3, n_max_props + 1):
            nn = f"{n:02d}"
            ext = "b08" if n <= 8 else "b16"
            ok = download(f"{BASE}/{name}{nn}.{ext}", ROOT / "properties" / f"{name}{nn}.{ext}")
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
