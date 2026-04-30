# Tests

```bash
pytest tests/        # all tests (DB tests fail if data not downloaded)
pytest tests/otdb/   # only Graz order type database integration tests
```

## Structure

| Path | Description |
|------|-------------|
| `test_core.py` | Unit tests for core representations (PointSet, BigLambda, SmallLambda) |
| `test_io.py` | Unit tests for readers/writers |
| `test_algorithms.py` | Unit tests for algorithms (polygon count, crossings, unify, …) |
| `otdb/` | Integration tests against the Graz order type database |

## Graz order type database

Integration tests verify computed properties against the
[Graz order type database](http://www.ist.tugraz.at/staff/aichholzer/research/rp/triangulations/ordertypes/).
Download the data files before running those tests:

```bash
python3 tests/otdb/download.py          # download n=3..9
python3 tests/otdb/download.py --also10 # also download n=10 (~3 GB uncompressed)
```

Files are saved to `tests/otdb/otypes/` and `tests/otdb/properties/` (both gitignored).
Tests fail with a clear message if the data files are not present.
