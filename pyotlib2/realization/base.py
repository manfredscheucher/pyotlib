"""Abstract base class for realization testers."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.point_set import PointSet


class Undecided(Exception):
    """Raised when a tester cannot determine realizability."""
    pass


class RealizationTester(ABC):
    """Base class for realizability testers.

    Supports a chain-of-responsibility pattern: if a tester cannot decide,
    it delegates to a parent tester.
    """

    def __init__(self, parent: Optional["RealizationTester"] = None):
        self.parent = parent

    def is_realizable(self, ot: SmallLambda) -> Optional[bool]:
        """Return True if realizable, False if not, None if unknown."""
        try:
            return self._test(ot)
        except Undecided:
            if self.parent is not None:
                return self.parent.is_realizable(ot)
            return None

    @abstractmethod
    def _test(self, ot: SmallLambda) -> bool:
        """Subclass-specific test.  Raise Undecided if inconclusive."""
        ...
