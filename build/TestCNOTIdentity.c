/*
 * harness_2q_float.c — 2-qubit symbolic harness, IEEE 754 encoding.
 *
 * The state of two qubits lives in the Hilbert space C^4 and is represented
 * by four complex amplitudes (amp00..amp11, first index = qubit q1, second
 * index = qubit q2). Each Q# gate is a fixed, manually reviewed linear
 * transformation over these amplitudes (encoding (ii) of the paper, enabled
 * in ESBMC via --floatbv). Numerical stability is asserted after every gate;
 * the property-specific assertion is injected at the end.
 */
#include <math.h>

#define INV_SQRT2 0.70710678118654752440
#define EPS_NORM  0.001
#define EPS_AMP   0.001

typedef struct { double real; double imag; } complex_t;

/* Hilbert space C^4 (2 qubits): |q1 q2>. */
typedef struct {
    complex_t amp00; complex_t amp01;
    complex_t amp10; complex_t amp11;
} system_2q_t;

/* Physical invariant: the state must remain normalized after every gate. */
void check_stability_2q(system_2q_t s) {
    double norm_sq = (s.amp00.real * s.amp00.real + s.amp00.imag * s.amp00.imag) +
                     (s.amp01.real * s.amp01.real + s.amp01.imag * s.amp01.imag) +
                     (s.amp10.real * s.amp10.real + s.amp10.imag * s.amp10.imag) +
                     (s.amp11.real * s.amp11.real + s.amp11.imag * s.amp11.imag);
    __ESBMC_assert(norm_sq >= 1.0 - EPS_NORM && norm_sq <= 1.0 + EPS_NORM,
                   "numerical stability: norm not preserved in C^4");
}

/* CNOT with control q1, target q2: |10> <-> |11>. */
system_2q_t apply_CNOT(system_2q_t s) {
    system_2q_t next = s;
    next.amp10 = s.amp11;
    next.amp11 = s.amp10;
    return next;
}

/* Hadamard on q1: mixes |0x> with |1x>. */
system_2q_t apply_H_q1(system_2q_t s) {
    system_2q_t next;
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

/* Pauli-X on q1: |0x> <-> |1x>. */
system_2q_t apply_X_q1(system_2q_t s) {
    system_2q_t next = s;
    next.amp00 = s.amp10; next.amp10 = s.amp00;
    next.amp01 = s.amp11; next.amp11 = s.amp01;
    return next;
}

/* Pauli-X on q2: |x0> <-> |x1>. */
system_2q_t apply_X_q2(system_2q_t s) {
    system_2q_t next = s;
    next.amp00 = s.amp01; next.amp01 = s.amp00;
    next.amp10 = s.amp11; next.amp11 = s.amp10;
    return next;
}

static _Bool close_to(double x, double ref) {
    return x >= ref - EPS_AMP && x <= ref + EPS_AMP;
}

int main() {
    system_2q_t s;
    /* Initial state |00>. */
    s.amp00.real = 1.0; s.amp00.imag = 0.0;
    s.amp01.real = 0.0; s.amp01.imag = 0.0;
    s.amp10.real = 0.0; s.amp10.imag = 0.0;
    s.amp11.real = 0.0; s.amp11.imag = 0.0;

    /* State preparation (from the '@prepare' directive). */


    system_2q_t s_ref = s;
    (void)s_ref;

    /* === TRANSLATED QUANTUM LOGIC (from Q#) === */
    s = apply_CNOT(s); check_stability_2q(s);
    s = apply_CNOT(s); check_stability_2q(s);
    /* === END OF TRANSLATED QUANTUM LOGIC === */

    /* === PROPERTY UNDER VERIFICATION === */
    __ESBMC_assert(close_to(s.amp00.real, s_ref.amp00.real) && close_to(s.amp00.imag, s_ref.amp00.imag) &&
                   close_to(s.amp01.real, s_ref.amp01.real) && close_to(s.amp01.imag, s_ref.amp01.imag) &&
                   close_to(s.amp10.real, s_ref.amp10.real) && close_to(s.amp10.imag, s_ref.amp10.imag) &&
                   close_to(s.amp11.real, s_ref.amp11.real) && close_to(s.amp11.imag, s_ref.amp11.imag),
                   "functional equivalence: final state != reference state");

    return 0;
}
