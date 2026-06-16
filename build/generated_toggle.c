#include <math.h>

/* 1. Definição da Estrutura de Amplitude Complexa */
typedef struct {
    double real;
    double imag;
} complex_t;

/* 2. Definição do Estado do Qubit (Espaço de Hilbert C^2) */
typedef struct {
    complex_t alpha; // Estado |0>
    complex_t beta;  // Estado |1>
} qubit_state_t;

/* 3. Verificador de Estabilidade Numérica (Invariante de Norma) */
void check_stability(qubit_state_t q) {
    double norm_sq = (q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag) +
                     (q.beta.real * q.beta.real + q.beta.imag * q.beta.imag);
    
    __ESBMC_assert(norm_sq >= 0.999 && norm_sq <= 1.001, "ERRO: Instabilidade Numerica");
}

/* 4. Operador Unitário: Porta Pauli-X */
qubit_state_t apply_X(qubit_state_t q) {
    qubit_state_t next;
    next.alpha = q.beta;
    next.beta  = q.alpha;
    return next;
}

int main() {
    qubit_state_t q;

    /* Estado Inicial Fixo: |0> puro */
    q.alpha.real = 1.0; q.alpha.imag = 0.0;
    q.beta.real  = 0.0; q.beta.imag  = 0.0;

    qubit_state_t initial_q = q;

    /* === INÍCIO DA LÓGICA QUÂNTICA TRADUZIDA === */
      // PrepareQubit ignorado: assumindo estado puro |0> fixado no template
  q = apply_X(q);
  check_stability(q); // Verifica a física
  q = apply_X(q);
  check_stability(q); // Verifica a física
  // Reset ignorado na validação do estado atual
    /* === FIM DA LÓGICA QUÂNTICA TRADUZIDA === */

    /* Verificação Formal Final */
    __ESBMC_assert(q.alpha.real == initial_q.alpha.real && 
                   q.beta.real == initial_q.beta.real, 
                   "Identidade quântica falhou");

    return 0;
}