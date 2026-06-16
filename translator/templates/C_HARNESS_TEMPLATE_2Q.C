#include <math.h>

#define INV_SQRT2 0.70710678118654752440

typedef struct { double real; double imag; } complex_t;

/* Espaço de Hilbert C^4 (2 Qubits) */
typedef struct {
    complex_t amp00; complex_t amp01;
    complex_t amp10; complex_t amp11;
} system_2q_t;

void check_stability_2q(system_2q_t s) {
    double norm_sq = (s.amp00.real * s.amp00.real + s.amp00.imag * s.amp00.imag) +
                     (s.amp01.real * s.amp01.real + s.amp01.imag * s.amp01.imag) +
                     (s.amp10.real * s.amp10.real + s.amp10.imag * s.amp10.imag) +
                     (s.amp11.real * s.amp11.real + s.amp11.imag * s.amp11.imag);
    __ESBMC_assert(norm_sq >= 0.999 && norm_sq <= 1.001, "ERRO: Instabilidade Numerica no C^4");
}

system_2q_t apply_CNOT(system_2q_t s) {
    system_2q_t next = s;
    next.amp10 = s.amp11;
    next.amp11 = s.amp10;
    return next;
}

system_2q_t apply_H_2q(system_2q_t s) {
    system_2q_t next;
    // Hadamard no primeiro qubit (00 <-> 10 e 01 <-> 11)
    next.amp00.real = INV_SQRT2 * (s.amp00.real + s.amp10.real);
    next.amp00.imag = INV_SQRT2 * (s.amp00.imag + s.amp10.imag);
    next.amp10.real = INV_SQRT2 * (s.amp00.real - s.amp10.real);
    next.amp10.imag = INV_SQRT2 * (s.amp00.imag - s.amp10.imag);
    
    next.amp01.real = INV_SQRT2 * (s.amp01.real + s.amp11.real);
    next.amp01.imag = INV_SQRT2 * (s.amp01.imag + s.amp11.imag);
    next.amp11.real = INV_SQRT2 * (s.amp01.real - s.amp11.real);
    next.amp11.imag = INV_SQRT2 * (s.amp01.imag - s.amp11.imag);
    return next;
}

int main() {
    system_2q_t s;
    /* Estado Inicial Fixo: |00> puro */
    s.amp00.real = 1.0; s.amp00.imag = 0.0;
    s.amp01.real = 0.0; s.amp01.imag = 0.0;
    s.amp10.real = 0.0; s.amp10.imag = 0.0;
    s.amp11.real = 0.0; s.amp11.imag = 0.0;

    system_2q_t initial_s = s;

    /* === INÍCIO DA LÓGICA QUÂNTICA TRADUZIDA === */
    /* <INJECT_LOGIC> */
    /* === FIM DA LÓGICA QUÂNTICA TRADUZIDA === */

    /* Verificação de Unitariedade (CNOT * CNOT = Identidade) */
    // _Bool amp00_ok = (s.amp00.real >= initial_s.amp00.real - 0.001) && (s.amp00.real <= initial_s.amp00.real + 0.001);
    // _Bool amp11_ok = (s.amp11.real >= initial_s.amp11.real - 0.001) && (s.amp11.real <= initial_s.amp11.real + 0.001);
    
    // __ESBMC_assert(amp00_ok && amp11_ok, "Propriedade de Unitariedade do CNOT falhou");

    /* Verificação de Unitariedade (Genérica) */
    // O template agora apenas garante que o estado final é fisicamente válido.
    // A asserção lógica específica do circuito é feita pelo ESBMC baseada no estado.
    check_stability_2q(s);

    return 0;
}