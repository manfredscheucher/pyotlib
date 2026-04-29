"""File writers for all pyotlib2 order-type formats."""

from __future__ import annotations
import json
import struct
from pathlib import Path
from typing import Iterable

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.utils import binomial


def write_order_types(
    ots: Iterable[SmallLambda],
    filepath: str | Path,
    fmt: Optional[str] = None,
) -> int:
    """Write order types to filepath.  Returns count written."""
    filepath = Path(filepath)
    if fmt is None:
        fmt = filepath.suffix.lstrip(".")

    byte_map = {"b08": 1, "b16": 2, "b32": 4, "b64": 8}
    if fmt in byte_map:
        return _write_point_binary(ots, filepath, bytes_per_coord=byte_map[fmt])

    fmt = fmt.lower()
    if fmt in ("lt", "txt", "lmd"):
        return _write_small_lambda_text(ots, filepath)
    elif fmt == "blt":
        return _write_big_lambda_text(ots, filepath)
    elif fmt in ("asc", "psz"):
        return _write_point_text_asc(ots, filepath)
    elif fmt == "json":
        return _write_point_text_json(ots, filepath)
    else:
        raise ValueError(f"Unknown format: {fmt!r}")


from typing import Optional


def _write_small_lambda_text(ots: Iterable[SmallLambda], filepath: Path) -> int:
    cnt = 0
    with open(filepath, "w") as f:
        for ot in ots:
            f.write(ot.to_string())
            f.write("\n")
            cnt += 1
    return cnt


def _write_big_lambda_text(ots: Iterable[SmallLambda], filepath: Path) -> int:
    cnt = 0
    with open(filepath, "w") as f:
        for ot in ots:
            f.write(ot.to_big_lambda().to_string() + "\n")
            cnt += 1
    return cnt


_STRUCT_FMT = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}


def _write_point_binary(
    ots: Iterable[SmallLambda], filepath: Path, bytes_per_coord: int
) -> int:
    fmt = _STRUCT_FMT[bytes_per_coord]
    cnt = 0
    with open(filepath, "wb") as f:
        for ot in ots:
            assert ot.realization is not None, "binary output requires a realization"
            for x, y in ot.realization:
                f.write(struct.pack(fmt, int(x)))
                f.write(struct.pack(fmt, int(y)))
            cnt += 1
    return cnt


def _write_point_text_asc(ots: Iterable[SmallLambda], filepath: Path) -> int:
    cnt = 0
    with open(filepath, "w") as f:
        for ot in ots:
            assert ot.realization is not None
            f.write(f"{ot.n}\n")
            for x, y in ot.realization:
                f.write(f"{x} {y}\n")
            cnt += 1
    return cnt


def _write_point_text_json(ots: Iterable[SmallLambda], filepath: Path) -> int:
    cnt = 0
    with open(filepath, "w") as f:
        for ot in ots:
            assert ot.realization is not None
            f.write(json.dumps([[int(x), int(y)] for x, y in ot.realization]) + "\n")
            cnt += 1
    return cnt
