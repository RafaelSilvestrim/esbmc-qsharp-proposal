/*
 * harness_1q_float.c — 1-qubit symbolic harness, IEEE 754 encoding.
 *
 * The state of one qubit |psi> = alpha|0> + beta|1> is represented by two
 * complex amplitudes stored as C doubles. Each Q# gate is a fixed, manually
 * reviewed linear transformation over these amplitudes (encoding (ii) of the
 * paper, enabled in ESBMC via --floatbv). Numerical stability
 * (|alpha|^2 + |beta|^2 = 1 within an explicit tolerance) is asserted after
 * every gate; the property-specific assertion is injected at the end.
 *
 * Tolerances: EPS_NORM bounds accumulated IEEE 754 rounding across the
 * circuit; EPS_AMP bounds the per-amplitude deviation in equivalence checks.
 */
#include <math.h>

#define INV_SQRT2 0.70710678118654752440
#define EPS_NORM  0.001
#define EPS_AMP   0.001

typedef struct { double real; double imag; } complex_t;
typedef struct { complex_t alpha; complex_t beta; } qubit_state_t;

/* Physical invariant: the state must remain normalized after every gate. */
void check_stability(qubit_state_t q) {
    double norm_sq = (q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag) +
                     (q.beta.real  * q.beta.real  + q.beta.imag  * q.beta.imag);
    __ESBMC_assert(norm_sq >= 1.0 - EPS_NORM && norm_sq <= 1.0 + EPS_NORM,
                   "numerical stability: norm not preserved");
}

/* Pauli-X: swap alpha and beta. */
qubit_state_t apply_X(qubit_state_t q) {
    qubit_state_t next;
    next.alpha = q.beta;
    next.beta  = q.alpha;
    return next;
}

/* Hadamard: alpha' = (alpha+beta)/sqrt(2), beta' = (alpha-beta)/sqrt(2). */
qubit_state_t apply_H(qubit_state_t q) {
    qubit_state_t next;
    next.alpha.real = INV_SQRT2 * (q.alpha.real + q.beta.real);
    next.alpha.imag = INV_SQRT2 * (q.alpha.imag + q.beta.imag);
    next.beta.real  = INV_SQRT2 * (q.alpha.real - q.beta.real);
    next.beta.imag  = INV_SQRT2 * (q.alpha.imag - q.beta.imag);
    return next;
}

/* Phase gate S: beta' = i * beta. */
qubit_state_t apply_S(qubit_state_t q) {
    qubit_state_t next = q;
    next.beta.real = -q.beta.imag;
    next.beta.imag =  q.beta.real;
    return next;
}

/* Pauli-Z: beta' = -beta. */
qubit_state_t apply_Z(qubit_state_t q) {
    qubit_state_t next = q;
    next.beta.real = -q.beta.real;
    next.beta.imag = -q.beta.imag;
    return next;
}

/* Non-Clifford T gate: beta' = e^{i pi/4} * beta = (1+i)/sqrt(2) * beta. */
qubit_state_t apply_T(qubit_state_t q) {
    qubit_state_t next = q;
    next.beta.real = INV_SQRT2 * (q.beta.real - q.beta.imag);
    next.beta.imag = INV_SQRT2 * (q.beta.real + q.beta.imag);
    return next;
}

static _Bool close_to(double x, double ref) {
    return x >= ref - EPS_AMP && x <= ref + EPS_AMP;
}

int main() {
    qubit_state_t q;
    /* Initial state |0>. */
    q.alpha.real = 1.0; q.alpha.imag = 0.0;
    q.beta.real  = 0.0; q.beta.imag  = 0.0;

    /* State preparation (from the '@prepare' directive), applied before the
     * reference snapshot so identity-type properties compare against the
     * prepared state, not against |0>. */


    qubit_state_t q_ref = q;
    (void)q_ref;

    /* === TRANSLATED QUANTUM LOGIC (from Q#) === */
    q = apply_H(q); check_stability(q);
    q = apply_H(q); check_stability(q);
    /* === END OF TRANSLATED QUANTUM LOGIC === */

    /* === PROPERTY UNDER VERIFICATION === */
    /* Component-wise assertions so a counterexample names the divergent
     * amplitude (e.g. a phase flip on |1> violates only the beta check). */
    __ESBMC_assert(close_to(q.alpha.real, q_ref.alpha.real) &&
                   close_to(q.alpha.imag, q_ref.alpha.imag),
                   "functional equivalence: alpha (|0>) amplitude diverges");
    __ESBMC_assert(close_to(q.beta.real,  q_ref.beta.real)  &&
                   close_to(q.beta.imag,  q_ref.beta.imag),
                   "functional equivalence: beta (|1>) amplitude diverges");

    return 0;
}
