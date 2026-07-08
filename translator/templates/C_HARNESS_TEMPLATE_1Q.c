#include <math.h>

/* Constante pré-calculada 1/sqrt(2) para evitar deadlock no Z3 */
#define INV_SQRT2 0.70710678118654752440

/* 1. Estruturas Complexas e Qubit */
typedef struct { double real; double imag; } complex_t;
typedef struct { complex_t alpha; complex_t beta; } qubit_state_t;

/* 2. Estabilidade Numérica */
void check_stability(qubit_state_t q) {
    double norm_sq = (q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag) +
                     (q.beta.real * q.beta.real + q.beta.imag * q.beta.imag);
    __ESBMC_assert(norm_sq >= 0.999 && norm_sq <= 1.001, "ERRO: Instabilidade Numerica");
}

/* 3. Portas Quânticas */
qubit_state_t apply_X(qubit_state_t q) {
    qubit_state_t next;
    next.alpha = q.beta;
    next.beta  = q.alpha;
    return next;
}

qubit_state_t apply_H(qubit_state_t q) {
    qubit_state_t next;
    next.alpha.real = INV_SQRT2 * (q.alpha.real + q.beta.real);
    next.alpha.imag = INV_SQRT2 * (q.alpha.imag + q.beta.imag);
    next.beta.real  = INV_SQRT2 * (q.alpha.real - q.beta.real);
    next.beta.imag  = INV_SQRT2 * (q.alpha.imag - q.beta.imag);
    return next;
}

qubit_state_t apply_S(qubit_state_t q) {
    qubit_state_t next = q;
    // Porta S: multiplica beta por i (real -> -imag, imag -> real)
    double temp_real = q.beta.real;
    next.beta.real = -q.beta.imag;
    next.beta.imag = temp_real;
    return next;
}

qubit_state_t apply_T(qubit_state_t q) {
    qubit_state_t next = q;
    // Porta T: multiplica beta por (1/sqrt(2) + i/sqrt(2))
    double temp_real = q.beta.real;
    double temp_imag = q.beta.imag;
    next.beta.real = (temp_real * INV_SQRT2) - (temp_imag * INV_SQRT2);
    next.beta.imag = (temp_real * INV_SQRT2) + (temp_imag * INV_SQRT2);
    return next;
}

int main() {
    qubit_state_t q;
    /* Estado Inicial Fixo: |0> puro */
    q.alpha.real = 1.0; q.alpha.imag = 0.0;
    q.beta.real  = 0.0; q.beta.imag  = 0.0;

    qubit_state_t initial_q = q;

    /* === INÍCIO DA LÓGICA QUÂNTICA TRADUZIDA === */
    /* <INJECT_LOGIC> */
    /* === FIM DA LÓGICA QUÂNTICA TRADUZIDA === */

    /* Verificação Formal Final (Com tolerância epsilon de 0.001) */
    _Bool alpha_ok = (q.alpha.real >= initial_q.alpha.real - 0.001) && (q.alpha.real <= initial_q.alpha.real + 0.001);
    _Bool beta_ok  = (q.beta.real >= initial_q.beta.real - 0.001) && (q.beta.real <= initial_q.beta.real + 0.001);
    
    __ESBMC_assert(alpha_ok && beta_ok, "Identidade quantica falhou");

    return 0;
}