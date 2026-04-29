# pyotlib2 — Python Order Type Library 2.0

Combinatorial geometry on abstract order types in the plane.

An **order type** encodes the orientation (clockwise / counterclockwise) of
every triple of a point set.  pyotlib2 operates on these purely combinatorial
objects — no concrete coordinates are needed for most computations.

## Installation

```bash
pip install -e ".[dev]"        # development install with test dependencies
pip install -e ".[scipy]"      # add scipy for nonlinear realization
pip install -e ".[sat]"        # add SAT solver for extension enumeration
```

Requires Python ≥ 3.9, numpy ≥ 1.24.

## Data files (pyotlib-data submodule)

A companion repo [pyotlib-data](https://github.com/manfredscheucher/pyotlib-data)
is included as a git submodule.  It contains a download script to fetch the
Aichholzer order-type database and integration tests that verify computed
properties against that data.

```bash
# clone with submodule
git clone --recurse-submodules https://github.com/manfredscheucher/pyotlib.git

# or, if already cloned without submodule:
git submodule update --init --recursive

# download the database files (n=3..9 by default, --also10 for n=10 otypes):
cd pyotlib-data
python3 download.py
```

Files use unsigned integer coordinates:
- `.b08` = 1 byte per coordinate (n ≤ 8)
- `.b16` = 2 bytes per coordinate (n = 9, 10)

**Do not use n=9/10 files for automated tests** — they contain ~150k/14M
configurations.

## Quick start

### Python / IPython

```python
from pyotlib2.io.readers import read_order_types
from pyotlib2.algorithms.unify import unify
from pyotlib2.algorithms.polygon_count import count_polygons, count_crossings

# Read from Aichholzer database (binary 8-bit format)
ots = list(read_order_types("pyotlib-data/otypes/otypes06.b08", n=6))

# Deduplicate (lex-min normalization)
unique = list(unify(ots))
print(f"{len(unique)} distinct order types for n=6")  # → 16

# Count empty pentagons for each OT
for ot in unique:
    print(count_polygons(ot.big_lambda, k=5, empty_only=True))

# Crossing number (= number of convex 4-gons) via k-edges formula
for ot in unique:
    print(count_crossings(ot))
```

### Command line

```bash
# Deduplicate order types
pyotlib2 unifyOT otypes06.b08 -n 6

# Count empty pentagons
pyotlib2 polygonCount otypes06.b08 -n 6 -k 5

# Count distinct 4-point sub-order-types
pyotlib2 countSubOTs otypes08.b08 -n 8 -k 4
```

## Architecture

```
pyotlib2/
├── core/
│   ├── point_set.py      PointSet    — concrete 2D coordinates (exact arithmetic)
│   ├── small_lambda.py   SmallLambda — rank matrix l[i,j] (numpy int32, n×n)
│   ├── big_lambda.py     BigLambda   — orientation array o[i,j,k] (numpy int8, n×n×n)
│   └── utils.py          sign, ceil_log2, invert_perm, …
├── io/
│   ├── readers.py        read_order_types()  (lt, blt, b08/16/32/64, asc, json)
│   └── writers.py        write_order_types()
├── algorithms/
│   ├── polygon_count.py  empty/convex k-gon counting & enumeration
│   │                     crossing number via k-edges formula (O(n²))
│   ├── crossings.py      crossing pairs and crossing families
│   ├── projective_class.py  flip-graph BFS for projective equivalence classes
│   ├── unify.py          lex-min deduplication
│   └── sub_order_types.py   k-point sub-OT enumeration
├── realization/
│   ├── base.py           abstract RealizationTester
│   ├── gp_tester.py      Grassmann-Plucker LP via GLPK
│   └── scipy_tester.py   nonlinear optimization via scipy
└── cli/
    ├── main.py           argparse entry point
    ├── commands.py       command implementations (also importable as functions)
    └── io_args.py        shared CLI I/O helpers
```

### Representations

Three equivalent representations of an order type; conversions are lossless:

| Class | Description | Storage |
|-------|-------------|---------|
| `PointSet` | concrete (x,y) coordinates | 2n integers |
| `BigLambda` | o[i,j,k] ∈ {−1,+1} for each ordered triple | numpy int8, n³ |
| `SmallLambda` | l[i,j] = #{k : p_k left of ray i→j} | numpy int32, n² |

`SmallLambda` is the canonical working representation.  `BigLambda` is used
for orientation queries.  Both use numpy arrays throughout; hot paths use
numpy vectorization (e.g. `to_small_lambda` via `np.sum(o==1, axis=2)`,
`get_extremal_points` via `np.where`, `_is_valid_abstract` via masked `np.all`).

### Key algorithms

- **`count_crossings`**: O(n²) k-edges formula on the rank matrix — no enumeration needed
- **`enumerate_triangles`**: splits candidates into left/right half-planes per edge,
  uses chirotope symmetry (swap b↔c for CW triangles), vectorized emptiness test
- **`enumerate_polygons`**: natural-labeling BFS (ported from old pyotlib), asserts
  natural labeling, O(n^k) with early pruning
- **`ProjectiveClass`**: BFS on flip graph, lex-min normalization at each step

## License

MIT — see [LICENSE](LICENSE).

## TODO

See [TODO.md](TODO.md) for planned features and known limitations.
