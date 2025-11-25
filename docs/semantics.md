# Semântica Operacional (MVP)

**Hipótese do MVP:** restringimos o programa Q# ao *basis* computacional e às portas determinísticas no *basis* (`X`) para demonstrar a tubulação completa Q# → C → ESBMC.

- **Estado de 1 qubit:** `q ∈ {0,1}`
- **Portas:**
  - `X(q)` → `q := ¬q`
- **Medição em Z:** `M(q)` → observa `q`
- **Asserção:** definida via `fail` no Q# e convertida para `assert` no C.

Isso permite verificar, por SMT, propriedades determinísticas (ex.: `X∘X = I`). Etapas futuras incluem tabela de estabilizadores (Clifford completo) e probabilidades de medição.
