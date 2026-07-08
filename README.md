# ESBMC-Q#: Symbolic Formal Verification of Quantum Circuits

Verify-Before-Execution (VBE) pipeline for quantum validation artifacts in the
post-quantum cryptography (PQC) migration: Q# programs are transpiled to
symbolic C harnesses, exhaustively verified with
[ESBMC](https://github.com/esbmc/esbmc) via Bounded Quantum Model Checking
(BQMC), and every verdict is materialized as a **signed, auditable JSON-LD
evidence record** that feeds an IM-PQC governance process.

This repository is the companion artifact of the paper *"Symbolic Formal
Verification of Quantum Circuits for Post-Quantum Cryptography Governance in
Critical Infrastructures"* (`main.tex`).

## Pipeline (4 stages)

```
E1 Q# code  ->  E2 qsharp2c.py  ->  E3 ESBMC (SMT)  ->  E4 signed evidence
   qsharp/      translator/         UNSAT/SAT/TIMEOUT    results/evidence/
                (C harness +                              + CI/CD gate
                 assertions)                              (exit code)
```

* **UNSAT** — property holds up to the bound *k*: artifact is **promoted**.
* **SAT** — counterexample found: artifact is **blocked** at the CI/CD gate.
* **TIMEOUT** — escalated to manual review (increase *k* or decompose).

## Amplitude encodings

The transpiler supports two encodings (Section IV of the paper):

| Encoding | Arithmetic | Used for | ESBMC flags |
|----------|-----------|----------|-------------|
| `float`  | IEEE 754 doubles | Numerical-stability invariants; models the arithmetic the classical control software actually executes | `--unwind 1 --z3 --floatbv` |
| `exact`  | Ring Z[ω]/√2^k, ω = e^{iπ/4} (integers only, zero tolerance) | Algebraic properties: unitarity and functional equivalence of Clifford+T operators (1 qubit) | `--unwind 16 --z3` |

## Requirements

* Python ≥ 3.8 (no external packages needed).
* [ESBMC](https://github.com/esbmc/esbmc/releases) ≥ 7.9 on `PATH`
  (or set the `ESBMC` environment variable). Results in the paper were
  produced with ESBMC v8.4.0 (arm64 macOS) and Z3 v4.16.0.

## Reproducing the paper

```bash
# Experiments table — all 8 experiments through the full gate, signed evidence:
python3 scripts/run_experiments.py           # -> results/experiments.{csv,md}

# Scalability benchmark (GHZ-n, concrete -> fully symbolic regimes):
python3 scripts/run_benchmark.py             # -> results/benchmark.{csv,md}

# Cross-validation of the C model against an independent simulator:
python3 scripts/crossval.py
```

Single-circuit usage (the CI/CD gate — exit code 0 = promote, 1 = block):

```bash
python3 governance/vbe_gate.py qsharp/TestBellState.qs            # UNSAT -> 0
python3 governance/vbe_gate.py qsharp/TestSIdentity.qs; echo $?   # SAT   -> 1
python3 governance/vbe_gate.py qsharp/TestTGate.qs --encoding exact
```

Manual two-step flow:

```bash
python3 translator/qsharp2c.py qsharp/TestHHIdentity.qs build/hh.c
esbmc build/hh.c --unwind 1 --z3 --floatbv
```

Evidence records can be independently checked:

```bash
python3 governance/sign_record.py verify results/evidence/TestSIdentity.jsonld
```

## Experiments

| Exp | Circuit | Property | Expected |
|-----|---------|----------|----------|
| 1   | X·X on \|0⟩ | identity | UNSAT |
| 2a  | H·H on \|0⟩ | identity | UNSAT |
| 2b  | CNOT·CNOT on \|00⟩ | identity/unitarity | UNSAT |
| 3   | H, CNOT on \|00⟩ | Bell fidelity (target amplitudes) | UNSAT |
| 4   | S·S on \|1⟩ (deliberate fault: S² = Z ≠ I) | identity | **SAT** |
| 5   | H on \|0⟩ (QRNG artifact) | uniformity P(0)=P(1)=½ | UNSAT |
| 6a  | H·T·T ≡ H·S (non-Clifford, float) | equivalence | UNSAT |
| 6b  | H·T·T ≡ H·S (non-Clifford, exact Z[ω]) | equivalence, zero tolerance | UNSAT |

## Repository layout

```
main.tex                 paper (IEEE 2-column)
qsharp/                  Q# circuits (E1) with @property/@prepare directives
translator/qsharp2c.py   Q# -> C transpiler (E2)
translator/templates/    C harnesses: 1q/2q IEEE 754, 1q exact Z[ω]
governance/vbe_gate.py   full-pipeline CI/CD gate (E2->E3->E4)
governance/sign_record.py  Ed25519 signing/verification of evidence records
governance/ed25519.py    dependency-free RFC 8032 implementation
scripts/run_experiments.py  reproduces the experiments table of the paper
scripts/run_benchmark.py    reproduces the scalability benchmark table
scripts/crossval.py      independent state-vector cross-validation
classical/               original classical MVP example (toggle_twice.c)
build/                   generated C harnesses (regenerable)
results/                 experiment data, benchmark data, signed evidence
docs/                    semantics notes, conformance tests, roadmap
```

## Q# source directives

The transpiler reads three comment directives from `.qs` files:

```qsharp
// @property: identity | uniform | bell | equiv_hs | stability
// @prepare:  X            // state preparation before the reference snapshot
// @encoding: float | exact
```

## Security note

The Ed25519 key under `governance/keys/` is a laboratory demonstration key
generated on first use; production deployments must keep the signing key in
an HSM or equivalent and use a hardened Ed25519 implementation.

## Citing

See `main.tex` for the full author list and reference format. Core tool
references: ESBMC ([TACAS'19](https://doi.org/10.1007/978-3-030-17502-3_15),
[TACAS'24](https://doi.org/10.1007/978-3-031-57256-2_24)).
