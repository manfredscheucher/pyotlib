# pyotlib2 — Python Order Type Library 2.0

Combinatorial geometry on abstract order types in the plane.

An **order type** encodes the orientation (clockwise / counterclockwise) of
every triple of a point set. pyotlib2 operates on these purely combinatorial
objects — no concrete coordinates are needed for most computations.

## Installation

```bash
pip install pyotlib2                    # core: numpy only
pip install 'pyotlib2[vis]'             # + interactive editor (PySide6) + plots (matplotlib)
pip install 'pyotlib2[sat]'             # + SAT-based OT extension (python-sat/CaDiCaL)
pip install 'pyotlib2[scipy]'           # + scipy realization & beautify-coords
pip install 'pyotlib2[all]'             # everything above
```

For development:
```bash
pip install -e ".[all,dev]"
```

Requires Python ≥ 3.10, numpy ≥ 1.24.

## Quick start

### Python / IPython

```python
from pyotlib2.io.readers import read_order_types
from pyotlib2.algorithms.unify import unify
from pyotlib2.algorithms.polygon_count import count_empty_kgons, count_crossings
from pyotlib2.algorithms.mrsw import count_empty_kgons_mrsw

# read from Graz order type database (binary 8-bit format)
ots = list(read_order_types("tests/otdb/otypes/otypes06.b08", n=6))

# deduplicate (lex-min normalization)
unique = list(unify(ots))
print(f"{len(unique)} distinct order types for n=6")  # → 16

# count empty pentagons (MRSW algorithm, O(k·n³))
for ot in unique:
    print(count_empty_kgons_mrsw(ot, k=5))

# crossing number via k-edges formula (O(n²), abstract)
for ot in unique:
    print(count_crossings(ot))

# enumerate all n+1 extensions
from pyotlib2.cli.commands import extend_abstract
extensions = list(extend_abstract(ot))
```

### Command line

```bash
# deduplicate order types
pyotlib2 unify otypes06.b08 -n 6

# count empty k-gons
pyotlib2 kgons otypes06.b08 -n 6 --k 5

# count distinct sub-configurations
pyotlib2 count-subconf otypes08.b08 -n 8 --sub-n 4

# enumerate all n+1 extensions
pyotlib2 extend-abstract otypes06.b08 -n 6

# test realizability
pyotlib2 realize otypes09.b08 -n 9

# test non-realizability via Grassmann-Plücker LP
pyotlib2 gp-test otypes09.b08 -n 9
```

## Architecture

```
pyotlib2/
├── core/
│   ├── point_set.py         PointSet     — concrete 2D coordinates (exact rational arithmetic)
│   ├── small_lambda.py      SmallLambda  — rank matrix l[i,j] (numpy int32, n×n)
│   ├── big_lambda.py        BigLambda    — orientation array o[i,j,k] (numpy int8, n×n×n)
│   └── utils.py             sign, ceil_log2, invert_perm, …
├── io/
│   ├── readers.py           read_order_types()  (lt, blt, b08/16/32/64, asc, json)
│   └── writers.py           write_order_types()
├── algorithms/
│   ├── polygon_count.py     empty/convex k-gon counting & enumeration,
│   │                        crossing number via k-edges formula (O(n²), abstract)
│   ├── mrsw.py              MRSW O(k·n³) k-hole counting (Mitchell/Rote/Sundaram/Woeginger 1995)
│   ├── crossings.py         crossing pairs and crossing families
│   ├── projective_class.py  flip-graph BFS for projective equivalence classes
│   ├── unify.py             lex-min deduplication
│   └── sub_order_types.py   k-point sub-OT enumeration
├── realization/
│   ├── base.py              abstract RealizationTester
│   ├── gp_tester.py         Grassmann-Plücker LP non-realizability test (GLPK)
│   ├── grid_search.py       randomized backtracking on integer grid
│   └── scipy_tester.py      nonlinear optimization via scipy
└── cli/
    ├── main.py              argparse entry point
    ├── commands.py          command implementations (also importable as Python functions)
    └── io_args.py           shared CLI I/O helpers
```

### Representations

Three equivalent representations; conversions are lossless:

| Class | Description | Storage |
|-------|-------------|---------|
| `PointSet` | concrete (x,y) coordinates | 2n integers |
| `BigLambda` | o[i,j,k] ∈ {−1,+1} for each ordered triple (chirotope) | numpy int8, n³ |
| `SmallLambda` | l[i,j] = #{k : p_k left of ray i→j} (rank matrix) | numpy int32, n² |

`SmallLambda` is the canonical working representation.
All orientations are strictly ±1 — the framework is non-degenerate (no 3 collinear points).

## CLI commands

| Command | Description |
|---------|-------------|
| `unify` | Deduplicate OTs (lex-min); `--projective` for projective classes |
| `lexmin` | Relabel to lex-min representative; `--projective` for PC representer |
| `sort` | Sort OTs lexicographically |
| `shuffle` | Shuffle OTs randomly |
| `enum-subconf` | Enumerate k-point sub-configurations |
| `count-subconf` | Count distinct k-point sub-configurations per OT |
| `find-subconf` | Find OTs containing specific sub-configurations |
| `enum-projective` | Enumerate all OTs in each projective class |
| `enum-natural` | Enumerate all natural-labeled (+ mirrored) variants |
| `kgons` | Count empty/convex k-gons (MRSW algorithm) |
| `properties` | Compute combinatorial properties |
| `realize` | Test realizability (grid search or scipy); `--pc` for projective class |
| `smart-realize` | Realize point-by-point (etherealization) |
| `gp-test` | Test non-realizability via Grassmann-Plücker LP |
| `minimize-coords` | Minimize coordinate magnitude (preserves OT) |
| `beautify-coords` | Beautify coordinates via gradient descent or Nelder-Mead |
| `walk-points` | Local search in coordinate space to minimize a property |
| `walk-abstract` | Local search on the flip graph (no coordinates needed) |
| `extend-abstract` | Enumerate all n+1 extensions; `--method recursive\|sat` |
| `extend-random` | Extend realized OTs by randomly placing one point |
| `plot` | Visualize order types as point set drawings |

## Extension enumeration

Starting from the unique n=3 order type, iterative extension recovers all order types:

| n | OTs | time (recursive) | time (SAT) |
|---|-----|-----------------|------------|
| 3 | 1 | — | — |
| 4 | 2 | <0.01s | 0.03s |
| 5 | 3 | <0.01s | <0.01s |
| 6 | 16 | 0.01s | 0.02s |
| 7 | 135 | 0.07s | 0.23s |
| 8 | 3315 | 1.3s | 4.7s |
| 9 | 158,830 | ~80s | ~5min |

The recursive method uses signotope pruning (port of Scheucher 2020,
<https://doi.org/10.7155/jgaa.00529>). For n ≤ 8 all abstract order types
are realizable; for n = 9 the first non-realizable abstract OTs appear
(158,830 abstract vs 158,817 realizable).

## Data files (Graz order type database)

Download before running integration tests:

```bash
python3 tests/otdb/download.py    # download n=3..9
pytest tests/otdb/                # run integration tests
```

## Tests

```bash
pytest tests/ -q -k "not slow"    # fast tests (~138, <1s)
pytest tests/ -q                  # all tests including slow ones
```

## License

MIT — see [LICENSE](LICENSE).
