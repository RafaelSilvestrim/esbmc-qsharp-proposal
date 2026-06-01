#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <assert.h>

/* 1. Definição da Estrutura de Amplitude Complexa */
/* Representa o domínio contínuo das amplitudes complexas em uma máquina digital [3, 4]. */
typedef struct {
    double real;
    double imag;
} complex_t;

/* 2. Definição do Estado do Qubit (Espaço de Hilbert C^2) [1, 4] */
typedef struct {
    complex_t alpha; // Estado |0>
    complex_t beta;  // Estado |1>
} qubit_state_t;

/* 3. Verificador de Estabilidade Numérica (Invariante de Norma) */
/* Essencial para garantir a admissibilidade física e unitariedade [5, 6]. */
void check_stability(qubit_state_t q) {
    double norm_sq = (q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag) +
                     (q.beta.real * q.beta.real + q.beta.imag * q.beta.imag);
    
    /* Propriedade Φ: A norma deve ser 1.0. 
       O ESBMC usará QF_FP para buscar caminhos onde ocorra overflow/underflow [2, 7]. */
    __ESBMC_assert(norm_sq >= 0.999 && norm_sq <= 1.001, "ERRO: Instabilidade Numérica / Quebra de Unitariedade");
}

/* 4. Exemplo de Operador Unitário Abstraído (Porta de Hadamard) [5] */
qubit_state_t apply_hadamard(qubit_state_t q) {
    qubit_state_t next;
    double inv_sqrt2 = 1.0 / sqrt(2.0);
    
    // H|0> = (|0> + |1>)/sqrt(2), H|1> = (|0> - |1>)/sqrt(2)
    next.alpha.real = inv_sqrt2 * (q.alpha.real + q.beta.real);
    next.alpha.imag = inv_sqrt2 * (q.alpha.imag + q.beta.imag);
    next.beta.real  = inv_sqrt2 * (q.alpha.real - q.beta.real);
    next.beta.imag  = inv_sqrt2 * (q.alpha.imag - q.beta.imag);
    
    return next;
}

int main() {
    /* 5. Injeção de Não-Determinismo [8, 9] */
    /* O solver explora todos os estados iniciais simbolicamente. */
    qubit_state_t q;
    q.alpha.real = __VERIFIER_nondet_double();
    q.alpha.imag = __VERIFIER_nondet_double();
    q.beta.real  = __VERIFIER_nondet_double();
    q.beta.imag  = __VERIFIER_nondet_double();

    /* 6. Pré-condição: O estado inicial deve ser válido [10] */
    double initial_norm = (q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag) +
                          (q.beta.real * q.beta.real + q.beta.imag * q.beta.imag);
    __ESBMC_assume(initial_norm >= 0.999 && initial_norm <= 1.001);

    /* 7. Ciclo de Verificação */
    q = apply_hadamard(q);
    check_stability(q); // Verifica se a precisão do double manteve a física do sistema

    return 0;
}