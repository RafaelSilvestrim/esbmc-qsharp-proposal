# Conformance Tests

Two complementary levels keep the transpiled C model honest.

## 1. End-to-end expected verdicts

`scripts/run_experiments.py` runs every experiment through the full gate and
fails (exit 1) if any verdict differs from the expected column:

| Exp | Circuit | Property | Expected |
|-----|---------|----------|----------|
| 1   | X·X on \|0⟩ | identity | UNSAT |
| 2a  | H·H on \|0⟩ | identity | UNSAT |
| 2b  | CNOT·CNOT on \|00⟩ | identity | UNSAT |
| 3   | H, CNOT on \|00⟩ | bell | UNSAT |
| 4   | S·S on \|1⟩ (fault) | identity | **SAT** |
| 5   | H on \|0⟩ (QRNG) | uniform | UNSAT |
| 6a  | H·T·T (float) | equiv_hs | UNSAT |
| 6b  | H·T·T (exact) | equiv_hs | UNSAT |

Experiment 4 doubles as a *negative control*: it demonstrates that the
pipeline does not vacuously return UNSAT and that counterexamples name the
divergent amplitude.

## 2. Cross-validation against an independent simulator

`scripts/crossval.py` recomputes every expected state with an independent,
dependency-free state-vector simulator (complex matrices, no code shared
with the templates) and additionally validates the exact Z[ω] ring
operations against complex arithmetic. All 12 checks must PASS.

## Running

```bash
python3 scripts/run_experiments.py && python3 scripts/crossval.py
```

Manual fault-injection exercise: remove one `X(q);` from
`qsharp/TestXXIdentity.qs` (the verdict must flip to SAT), or change
`@prepare: X` in `qsharp/TestSIdentity.qs` and observe the counterexample
move from the β to the α amplitude.
