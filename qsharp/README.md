# ESBMC-QSharp: Verificação Formal de Circuitos Quânticos

Este projeto implementa uma pipeline de tradução automática entre **Q# (Quantum Development Kit)** e **C (para verificação via ESBMC)**. O objetivo é realizar a verificação formal de algoritmos quânticos, provando a correção de portas, propriedades de unitariedade e estados de emaranhamento, superando as limitações dos simuladores estatísticos.



## Estrutura do Projeto
- `qsharp/`: Contém os algoritmos quânticos em linguagem Q#.
- `translator/`: Contém o tradutor `qsharp2c.py` e os moldes (`templates/`) que convertem o código quântico para um modelo matemático verificável.
- `build/`: Local onde o código C gerado e pronto para a verificação é armazenado.

## Como Executar os Experimentos
O fluxo de trabalho foi automatizado para permitir a validação rápida de circuitos.

### Comando Único de Execução
Para rodar qualquer experimento, utilize o seguinte comando no terminal (substituindo pelo nome do arquivo desejado):

```bash
python3 translator/qsharp2c.py qsharp/<NOME_DO_TESTE>.qs build/resultado.c && \
esbmc build/resultado.c --unwind 1 --z3 --floatbv