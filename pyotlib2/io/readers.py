"""File readers for all pyotlib2 order-type formats.

Supported formats:
  lt / txt   — SmallLambda text (space-separated n×n matrix, one OT per n lines)
  blt        — BigLambda text (one line of '+'/'-' per OT)
  pb / b08 / b16 / b32 / b64  — binary point coordinates
  asc / psz  — ASCII point set text
  json       — JSON point list

Usage::

    for ot in read_order_types("otypes06.b08", n=6):
        print(ot.to_string())
"""

from __future__ import annotations
import struct
import json
from pathlib import Path
from typing import Iterator, Optional

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.big_lambda import BigLambda
from pyotlib2.core.point_set import PointSet
from pyotlib2.core.utils import binomial


def read_order_types(
    filepath: str | Path,
    fmt: Optional[str] = None,
    n: Optional[int] = None,
) -> Iterator[SmallLambda]:
    """Yield SmallLambda objects from filepath.

    Parameters
    ----------
    filepath:
        Path to the input file.
    fmt:
        File format string.  If None, guessed from the file extension.
        Supported: ``lt``, ``txt``, ``blt``, ``pb``, ``b08``, ``b16``, ``b32``,
        ``b64``, ``asc``, ``psz``, ``json``.
    n:
        Number of points per order type.  Required for binary formats if it
        cannot be inferred from the filename.
    """
    filepath = Path(filepath)
    if fmt is None:
        fmt = filepath.suffix.lstrip(".")

    # normalise aliases
    byte_map = {"b08": 1, "b16": 2, "b32": 4, "b64": 8}
    if fmt in byte_map:
        yield from _read_point_binary(filepath, n=n, bytes_per_coord=byte_map[fmt])
        return

    fmt = fmt.lower()
    if fmt in ("lt", "txt", "lmd"):
        yield from _read_small_lambda_text(filepath, n=n)
    elif fmt == "blt":
        yield from _read_big_lambda_text(filepath, n=n)
    elif fmt == "pb":
        yield from _read_point_binary(filepath, n=n, bytes_per_coord=1)
    elif fmt in ("asc", "psz"):
        yield from _read_point_text_asc(filepath, n=n)
    elif fmt == "json":
        yield from _read_point_text_json(filepath, n=n)
    else:
        raise ValueError(f"Unknown format: {fmt!r}")


# ---------------------------------------------------------------------------
# SmallLambda text reader
# ---------------------------------------------------------------------------

def _read_small_lambda_text(
    filepath: Path, n: Optional[int]
) -> Iterator[SmallLambda]:
    with open(filepath, "r") as f:
        # auto-detect n if not given
        if n is None:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                n = len(line.split())
                break
            f.seek(0)

        while True:
            lines = []
            for _ in range(n):
                line = f.readline()
                if line == "":
                    if lines:
                        break  # partial read at EOF — ignore
                    return  # clean EOF
                # skip blank and comment lines
                while not line.strip() or line.strip().startswith("#"):
                    line = f.readline()
                    if line == "":
                        return
                lines.append(line)
            if len(lines) != n:
                return
            string = "".join(lines)
            yield SmallLambda.from_string(n, string)


# ---------------------------------------------------------------------------
# BigLambda text reader
# ---------------------------------------------------------------------------

def _read_big_lambda_text(
    filepath: Path, n: Optional[int]
) -> Iterator[SmallLambda]:
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            L = len(line)
            if n is None:
                n = 3
                while binomial(n, 3) not in (L, L - 1):
                    n += 1
            # parse '+'/'-' string into orientation array
            chars = [c for c in line if c in "+-"]
            n3 = binomial(n, 3)
            assert len(chars) == n3, f"expected {n3} chars, got {len(chars)}"
            from itertools import combinations
            import numpy as np

            o = np.zeros((n, n, n), dtype=np.int8)
            for idx, (a, b, c) in enumerate(combinations(range(n), 3)):
                val = np.int8(1) if chars[idx] == "+" else np.int8(-1)
                o[a, b, c] = o[b, c, a] = o[c, a, b] = val
                o[a, c, b] = o[b, a, c] = o[c, b, a] = -val
            bl = BigLambda(n, o)
            yield bl.to_small_lambda()


# ---------------------------------------------------------------------------
# Binary point set reader (Aichholzer format)
# ---------------------------------------------------------------------------

_STRUCT_FMT = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}


def _read_point_binary(
    filepath: Path,
    n: Optional[int],
    bytes_per_coord: int,
) -> Iterator[SmallLambda]:
    assert n is not None, "n (number of points) is required for binary formats"
    fmt = _STRUCT_FMT[bytes_per_coord]
    size = bytes_per_coord
    with open(filepath, "rb") as f:
        while True:
            coords = []
            ok = True
            for _ in range(n):
                bx = f.read(size)
                by = f.read(size)
                if len(bx) < size or len(by) < size:
                    ok = False
                    break
                x = struct.unpack(fmt, bx)[0]
                y = struct.unpack(fmt, by)[0]
                coords.append((x, y))
            if not ok:
                return
            yield PointSet(n, coords).to_small_lambda()


# ---------------------------------------------------------------------------
# ASCII / PSZ text point set reader
# ---------------------------------------------------------------------------

def _read_point_text_asc(
    filepath: Path, n: Optional[int]
) -> Iterator[SmallLambda]:
    with open(filepath, "r") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        # skip comments
        while i < len(lines) and lines[i].strip().startswith("#"):
            i += 1
        if i >= len(lines):
            break
        cur_n = int(lines[i].strip())
        i += 1
        if n is not None:
            assert cur_n == n
        coords = []
        for _ in range(cur_n):
            while lines[i].strip().startswith("#"):
                i += 1
            x, y = map(int, lines[i].split())
            coords.append((x, y))
            i += 1
        yield PointSet(cur_n, coords).to_small_lambda()


# ---------------------------------------------------------------------------
# JSON point set reader
# ---------------------------------------------------------------------------

def _read_point_text_json(
    filepath: Path, n: Optional[int]
) -> Iterator[SmallLambda]:
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pts = json.loads(line)
            cur_n = len(pts)
            if n is not None:
                assert cur_n == n
            coords = [tuple(p) for p in pts]
            yield PointSet(cur_n, coords).to_small_lambda()
