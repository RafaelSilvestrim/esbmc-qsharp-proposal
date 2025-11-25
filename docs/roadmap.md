# Roadmap (MVP → v1)

- **MVP (agora)**: X no basis computacional; tradução para C; verificação via ESBMC.
- **v0.2**: adicionar CNOT(c,t) como `t := t XOR c` + múltiplos qubits booleanos.
- **v0.3**: tabela de estabilizadores (Clifford: H, S, CNOT) com medição em Z.
- **v0.4**: propriedades probabilísticas (Pr[violação] ≤ ε) e medições condicionais.
- **v1.0**: integração de tempo real (deadlines, WCET no wrapper clássico) e bateria de benchmarks.
