"""Unit tests for I/O: readers and writers."""

import json
import struct
import tempfile
from pathlib import Path

import pytest

from pyotlib2.core.point_set import PointSet
from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.io.readers import read_order_types
from pyotlib2.io.writers import write_order_types


SAMPLE_POINTS_4 = [(0, 0), (3, 0), (3, 3), (0, 3)]
SAMPLE_POINTS_4B = [(0, 0), (4, 0), (2, 3), (0, 3)]   # distinct OT from SAMPLE_POINTS_4
SAMPLE_POINTS_5 = [(0, 0), (4, 0), (4, 4), (0, 4), (1, 2)]  # non-degenerate interior pt


def make_sl(pts):
    ps = PointSet(len(pts), pts)
    return ps.to_small_lambda(lazy=False)


# ---------------------------------------------------------------------------
# SmallLambda text format
# ---------------------------------------------------------------------------

class TestSmallLambdaText:
    def test_roundtrip(self):
        sl = make_sl(SAMPLE_POINTS_4)
        with tempfile.NamedTemporaryFile(suffix=".lt", mode="w", delete=False) as f:
            path = Path(f.name)
        try:
            write_order_types([sl], path, fmt="lt")
            [sl2] = list(read_order_types(path, fmt="lt"))
            assert sl.compare(sl2) == 0
        finally:
            path.unlink(missing_ok=True)

    def test_multiple_ots(self):
        # Both n=4, so reader can auto-detect n from first row
        ots = [make_sl(SAMPLE_POINTS_4), make_sl(SAMPLE_POINTS_4B)]
        with tempfile.NamedTemporaryFile(suffix=".lt", mode="w", delete=False) as f:
            path = Path(f.name)
        try:
            write_order_types(ots, path, fmt="lt")
            loaded = list(read_order_types(path, fmt="lt"))
            assert len(loaded) == 2
        finally:
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# BigLambda text format
# ---------------------------------------------------------------------------

class TestBigLambdaText:
    def test_roundtrip(self):
        sl = make_sl(SAMPLE_POINTS_4)
        with tempfile.NamedTemporaryFile(suffix=".blt", mode="w", delete=False) as f:
            path = Path(f.name)
        try:
            write_order_types([sl], path, fmt="blt")
            [sl2] = list(read_order_types(path, fmt="blt"))
            # Compare via BigLambda string
            assert sl.to_big_lambda().to_string() == sl2.to_big_lambda().to_string()
        finally:
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

class TestJsonFormat:
    def test_roundtrip(self):
        pts = SAMPLE_POINTS_4
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            path = Path(f.name)
        ps = PointSet(len(pts), pts)
        sl = ps.to_small_lambda()
        sl.realization = pts  # ensure realization is set
        try:
            write_order_types([sl], path, fmt="json")
            [sl2] = list(read_order_types(path, fmt="json"))
            assert sl2.n == len(pts)
        finally:
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Binary point format (b08)
# ---------------------------------------------------------------------------

class TestBinaryFormat:
    def _write_binary(self, pts_list, bytes_per_coord=1):
        fmt = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}[bytes_per_coord]
        with tempfile.NamedTemporaryFile(suffix=".b08", delete=False) as f:
            path = Path(f.name)
        with open(path, "wb") as f:
            for pts in pts_list:
                for x, y in pts:
                    f.write(struct.pack(fmt, x))
                    f.write(struct.pack(fmt, y))
        return path

    def test_read_b08(self):
        pts = [(0, 0), (3, 0), (3, 3), (0, 3)]
        path = self._write_binary([pts])
        try:
            ots = list(read_order_types(path, fmt="b08", n=4))
            assert len(ots) == 1
            assert ots[0].n == 4
        finally:
            path.unlink(missing_ok=True)

    def test_read_multiple_b08(self):
        pts_list = [
            [(0, 0), (3, 0), (3, 3), (0, 3)],
            [(0, 0), (4, 0), (2, 3), (0, 3)],
        ]
        path = self._write_binary(pts_list)
        try:
            ots = list(read_order_types(path, fmt="b08", n=4))
            assert len(ots) == 2
        finally:
            path.unlink(missing_ok=True)

    def test_format_alias_b08(self):
        """fmt='b08' is equivalent to passing bytes_per_coord=1."""
        pts = [(0, 0), (6, 0), (6, 6), (0, 6), (1, 2)]
        path = self._write_binary([pts])
        try:
            ots = list(read_order_types(path, fmt="b08", n=5))
            assert len(ots) == 1
            assert ots[0]._is_valid_abstract()
        finally:
            path.unlink(missing_ok=True)
