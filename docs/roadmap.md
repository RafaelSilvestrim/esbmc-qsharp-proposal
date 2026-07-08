# Roadmap

Mirrors Section "Roadmap and Next Steps" of the paper.

## Done (current artifact, TRL 3 → 4)

- Q# → C transpiler with directive-driven property injection
  (`identity`, `uniform`, `bell`, `equiv_hs`, `stability`).
- IEEE 754 (`--floatbv`) encoding for numerical-stability invariants.
- Exact Z[ω]/√2^k encoding (1 qubit, Clifford+T): zero-tolerance algebraic
  verification of unitarity and functional equivalence.
- Non-Clifford experiment (T·T = S) and PQC-supporting QRNG artifact.
- Deliberate-fault negative control (S² ≠ I) with counterexample.
- Scalability benchmark: GHZ-n, concrete vs. fully symbolic initial states,
  explicit report of where SMT solving degrades.
- End-to-end governance loop: signed JSON-LD evidence records (Ed25519) and
  a CI/CD gate mapping UNSAT/SAT/TIMEOUT to promote/block/escalate.
- Cross-validation of the C model against an independent simulator.

## 2026–2027 (TRL 5)

- Multi-qubit non-Clifford support (Toffoli; T on n ≥ 2 qubits) — the
  regime where classical simulation becomes intractable.
- Exact encoding for n ≥ 2 qubits and exact equivalence proofs at scale.
- Formal soundness argument for the transpilation (C semantics vs. λ-Q#).
- k-induction for parametrized/iterative quantum programs.
- Full CI/CD automation of the technology gate; open-source release.

## 2027–2028 (TRL 6)

- Validation in a real defense scenario (IME/UFAM partnership; Brazilian
  Army and Navy cryptography laboratories).
- Integration with critical-system acquisition processes; submission to
  regulatory bodies (INMETRO, ABNT).
