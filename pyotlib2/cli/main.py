"""pyotlib2 CLI entry point.

Usage:
    pyotlib2 <command> [options]

Commands:
    unifyOT        Remove duplicate order types
    polygonCount   Count empty/convex k-gons
    countSubOTs    Count distinct k-point sub-order-types
    findSubOTs     Find OTs containing specific sub-order-types
    relabelOT      Relabel / compute lex-min representative
    sortOTs        Sort order types lexicographically
    shuffleOTs     Randomly shuffle order types
    realize        Test realizability of abstract order types
    propertyCount  Compute combinatorial properties

All commands can also be used as Python functions:
    from pyotlib2.cli import unify_ot, polygon_count, ...
"""

import argparse
import sys
from pyotlib2.cli import commands


def main():
    parser = argparse.ArgumentParser(
        prog="pyotlib2",
        description="Python Order Type Library 2 — abstract order type computations",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    commands.register_all(sub)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
