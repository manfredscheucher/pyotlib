# pyotlib2 TODO

## Near-term

- [ ] Port `ErdosSzekeresSaturated`: SAT-based order type extension (pycosat/cadical)
- [ ] Port `FilterExitEdges`: removable edge detection via rotation system
- [ ] Port `ProjectiveClass` fully (currently only basic flip graph)
- [ ] Port `UniversalOrderTypes`: coverage testing against complete OT database
- [ ] Port `Symmetries`: symmetric configuration generation
- [ ] Port SageMath scripts: pseudocircle drawing, primal/dual graph, GP tests
- [ ] Gurobi realization tester (replacing old CPlex)
- [ ] Pattern search optimizer (Hooke-Jeeves) for realization
- [ ] Improve GP realization tester (full LP formulation, not just 5-tuple check)
- [ ] `pyotlib2 extendAbstract`: extend OTs by one point (SAT-based)
- [ ] `math.comb` instead of custom `binomial` in utils.py (Python 3.8+);
      `math.lcm` instead of custom `lcm` (Python 3.9+)

## Algorithms (future research)

- [ ] **MRSW algorithm for abstract order types**:
  Mitchell, Rote, Sundaram, Woeginger (MRSW) give an efficient algorithm for
  counting empty convex k-gons on concrete point sets.  Their paper does not
  cover abstract order types, but with natural labeling (last point on convex
  hull — always guaranteed after abstract extension) all required orientation
  data is available directly from BigLambda without coordinates.  This would
  make the MRSW algorithm applicable to abstract order types for the first time.
  No existing literature on this generalization, but mathematically sound.

## Performance / Vectorization

- [ ] `PointSet.to_big_lambda`: vectorize triple-loop using numpy broadcasting —
      compute all C(n,3) orientations at once (det formula), then assign all 6
      chirotope symmetry entries via fancy indexing
- [ ] `BigLambda.is_valid`: vectorize chirotope axiom checks with numpy masks
      instead of O(n³) triple loop
- [ ] `BigLambda.get_rotation_system`: replace set comprehensions with `np.where`
- [ ] `SmallLambda.is_extremal_point` / `has_natural_labeling`: replace Python
      `any()`/`all()` generators with numpy operations
- [ ] `count_crossings`: replace dict accumulation loop with `np.bincount`
- [ ] Benchmark numpy vectorization vs lazy `any()` for containment tests;
      for large n numpy SIMD wins, for small n (≤9) lazy any() may be faster
- [ ] Cython extension for orientation triple computation (inner loop bottleneck)
- [ ] Parallel polygon enumeration for large n

## Infrastructure

- [ ] CI/CD with GitHub Actions (run tests on push)
- [ ] Conda package for easier installation
- [ ] Jupyter notebook examples
- [ ] Typed stubs (.pyi) for IDE support
