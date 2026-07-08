# Operational Semantics of the C Model

The transpiler `translator/qsharp2c.py` maps a restricted Q# fragment to a C
verification harness. The verified model is defined by the tuple
P = ⟨Σ, Σ₀, T, Φ⟩ (Section III of the paper): symbolic states Σ, initial
states Σ₀, gate-induced transitions T, and the injected property Φ.

## Supported Q# fragment

- Straight-line programs: a single `operation`, no loops, no conditionals.
- 1 or 2 qubits (`use q = Qubit();` or `use (q1, q2) = (Qubit(), Qubit());`).
- Gates: `X, H, S, T, Z` (1 qubit); `H, X` per qubit and `CNOT(q1, q2)`
  (2 qubits, control = first declared qubit).
- Measurement (`M`, `Measure`) or `Reset` terminates the *unitary region*:
  everything after it is outside the verified model. Properties refer to the
  pre-measurement state.

## State representation

**IEEE 754 encoding (`float`)** — each amplitude is a pair of `double`s
(real, imag). Gates are fixed linear transformations (see
`translator/templates/harness_{1q,2q}_float.c`). After every gate the norm
invariant |α|² + |β|² ∈ [1 − ε, 1 + ε] is asserted (ε = 10⁻³). Equivalence
assertions use an explicit per-amplitude tolerance. Verified with
`--floatbv`, so ESBMC reasons over genuine IEEE 754 arithmetic — including
rounding — exactly as executed by classical control software.

**Exact encoding (`exact`)** — Clifford+T amplitudes over one qubit lie in
the ring Z[ω]/√2^k with ω = e^{iπ/4} (Kliuchnikov–Maslov–Mosca
representation). Each amplitude is four integers (c₀..c₃) plus a shared
denominator exponent k:

    amplitude = (c₀ + c₁ω + c₂ω² + c₃ω³) / √2^k

Gate actions are integer-only: X swaps amplitudes; Z, S, T multiply β by
ω⁴ = −1, ω², ω (coefficient rotations with sign wrap); H adds/subtracts
numerators and increments k. Unitarity is checked exactly:
|α|² + |β|² = 2^k with zero √2-component. No tolerances exist in this
encoding, so UNSAT is an exact algebraic proof. See
`translator/templates/harness_1q_exact.c`.

## Properties (Φ)

| Directive | Assertion |
|-----------|-----------|
| `identity` | final state = reference snapshot (taken after `@prepare` gates) |
| `uniform`  | \|α\|² = \|β\|² = ½ (QRNG unbiasedness) |
| `bell`     | amplitudes of (\|00⟩+\|11⟩)/√2 |
| `equiv_hs` | final state = (S·H)\|0⟩ (checks T·T = S) |
| `stability` | norm preservation only |

## Soundness status

The gate encodings are fixed, manually reviewed, and cross-validated against
an independent state-vector simulator (`scripts/crossval.py`), which also
checks the Z[ω] ring operations against complex arithmetic. A formal,
by-construction soundness argument relating the generated C semantics to
λ-Q# remains future work (paper, Section "Threats to Validity").
