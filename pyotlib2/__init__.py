"""
pyotlib2 — Python Order Type Library 2.0
Abstract order type computations in the plane.
"""

from pyotlib2.core.point_set import PointSet
from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.big_lambda import BigLambda
from pyotlib2.io.readers import read_order_types
from pyotlib2.io.writers import write_order_types

__version__ = "2.0.0"
__all__ = ["PointSet", "SmallLambda", "BigLambda", "read_order_types", "write_order_types"]
