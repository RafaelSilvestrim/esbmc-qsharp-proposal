# Conformance Tests (PASS/FAIL)

| Caso | Entrada | Q# (esperado) | ESBMC (esperado) | Status |
|------|---------|----------------|------------------|--------|
| X∘X = I | `initial ∈ {0,1}` | `M == initial` | `assert(final == initial)` | PASS |
| X = I (remover 1 X) | `initial ∈ {0,1}` | `M == initial` (falso em `initial=0`) | `assert(final == initial)` | FAIL |
| X∘X∘X = X | `initial ∈ {0,1}` | `M == ¬initial` | `assert(final == initial)` | FAIL |

Como rodar:
1. Edite a região traduzível em `qsharp/TestXXIdentity.qs` (adicione/remova `X(q);`).
2. Gere o C: `python3 translator/qsharp2c.py qsharp/TestXXIdentity.qs build/generated_toggle.c`.
3. Verifique: `esbmc build/generated_toggle.c --unwind 1`.
