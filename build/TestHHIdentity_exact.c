/*
 * harness_1q_exact.c — 1-qubit symbolic harness, exact rational encoding.
 *
 * Encoding (i) of the paper: Clifford+T amplitudes over one qubit live in
 * the ring Z[w]/sqrt(2)^k, where w = e^{i*pi/4} is a primitive 8th root of
 * unity (w^4 = -1). Every amplitude is represented exactly as
 *
 *     (c0 + c1*w + c2*w^2 + c3*w^3) / sqrt(2)^k
 *
 * with integer coefficients c0..c3 and a global denominator exponent k
 * shared by both amplitudes (this is the standard exact representation for
 * Clifford+T circuits, cf. Kliuchnikov-Maslov-Mosca). All gate applications
 * and property checks are integer-only: no floating point, no tolerances.
 * An UNSAT verdict is therefore an exact algebraic proof up to the bound.
 *
 * Gate actions on the numerators (k unchanged unless noted):
 *   X: swap alpha/beta          Z: beta *= w^4 = -1
 *   S: beta *= w^2 (= i)        T: beta *= w
 *   H: alpha' = alpha + beta, beta' = alpha - beta, k += 1
 *      (the 1/sqrt(2) factor is absorbed by incrementing k)
 *
 * Verify with: esbmc <file> --unwind 16 --z3
 * (the small constant-bound loop in normalize_k requires unwinding).
 */

typedef struct { long long c0, c1, c2, c3; } zw_t;          /* element of Z[w] */
typedef struct { zw_t alpha; zw_t beta; int k; } qstate_t;  /* amp = zw / sqrt(2)^k */

/* Multiply an element of Z[w] by sqrt(2) = w - w^3 (exact). */
zw_t zw_mul_sqrt2(zw_t a) {
    zw_t r;
    r.c0 = a.c1 - a.c3;
    r.c1 = a.c0 + a.c2;
    r.c2 = a.c1 + a.c3;
    r.c3 = a.c2 - a.c0;
    return r;
}

/* |z|^2 = P0 + P1*sqrt(2) with integer P0, P1 (P2 = 0 and P3 = -P1 hold
 * identically for z * conj(z), so only P0 and P1 are returned). */
long long zw_norm_p0(zw_t a) {
    return a.c0*a.c0 + a.c1*a.c1 + a.c2*a.c2 + a.c3*a.c3;
}
long long zw_norm_p1(zw_t a) {
    return a.c0*a.c1 - a.c0*a.c3 + a.c1*a.c2 + a.c2*a.c3;
}

/* Exact unitarity: |alpha|^2 + |beta|^2 must equal sqrt(2)^k squared-scaled,
 * i.e. the integer part equals 2^k and the sqrt(2) part vanishes. */
void check_unitarity_exact(qstate_t q) {
    long long p0 = zw_norm_p0(q.alpha) + zw_norm_p0(q.beta);
    long long p1 = zw_norm_p1(q.alpha) + zw_norm_p1(q.beta);
    __ESBMC_assert(p0 == (1LL << q.k) && p1 == 0,
                   "exact unitarity violated");
}

qstate_t apply_X_exact(qstate_t q) {
    qstate_t next = q;
    next.alpha = q.beta;
    next.beta  = q.alpha;
    return next;
}

qstate_t apply_Z_exact(qstate_t q) {
    qstate_t next = q;
    next.beta.c0 = -q.beta.c0; next.beta.c1 = -q.beta.c1;
    next.beta.c2 = -q.beta.c2; next.beta.c3 = -q.beta.c3;
    return next;
}

/* S: beta *= w^2, i.e. coefficient rotation by 2 with sign wrap (w^4 = -1). */
qstate_t apply_S_exact(qstate_t q) {
    qstate_t next = q;
    next.beta.c0 = -q.beta.c2;
    next.beta.c1 = -q.beta.c3;
    next.beta.c2 =  q.beta.c0;
    next.beta.c3 =  q.beta.c1;
    return next;
}

/* T: beta *= w, i.e. coefficient rotation by 1 with sign wrap. */
qstate_t apply_T_exact(qstate_t q) {
    qstate_t next = q;
    next.beta.c0 = -q.beta.c3;
    next.beta.c1 =  q.beta.c0;
    next.beta.c2 =  q.beta.c1;
    next.beta.c3 =  q.beta.c2;
    return next;
}

qstate_t apply_H_exact(qstate_t q) {
    qstate_t next;
    next.alpha.c0 = q.alpha.c0 + q.beta.c0;
    next.alpha.c1 = q.alpha.c1 + q.beta.c1;
    next.alpha.c2 = q.alpha.c2 + q.beta.c2;
    next.alpha.c3 = q.alpha.c3 + q.beta.c3;
    next.beta.c0  = q.alpha.c0 - q.beta.c0;
    next.beta.c1  = q.alpha.c1 - q.beta.c1;
    next.beta.c2  = q.alpha.c2 - q.beta.c2;
    next.beta.c3  = q.alpha.c3 - q.beta.c3;
    next.k = q.k + 1;
    return next;
}

/* Rescale a state to a larger denominator exponent so two states can be
 * compared coefficient-wise (multiplying numerators by sqrt(2) once per
 * missing power keeps the represented amplitudes unchanged). */
qstate_t normalize_k(qstate_t q, int target_k) {
    for (int i = q.k; i < target_k; ++i) {
        q.alpha = zw_mul_sqrt2(q.alpha);
        q.beta  = zw_mul_sqrt2(q.beta);
        q.k = q.k + 1;
    }
    return q;
}

_Bool zw_eq(zw_t a, zw_t b) {
    return a.c0 == b.c0 && a.c1 == b.c1 && a.c2 == b.c2 && a.c3 == b.c3;
}

/* Exact state equality (no tolerance). */
_Bool state_eq_exact(qstate_t a, qstate_t b) {
    int k = a.k > b.k ? a.k : b.k;
    a = normalize_k(a, k);
    b = normalize_k(b, k);
    return zw_eq(a.alpha, b.alpha) && zw_eq(a.beta, b.beta);
}

int main() {
    qstate_t q;
    /* Initial state |0>: alpha = 1, beta = 0, k = 0. */
    q.alpha.c0 = 1; q.alpha.c1 = 0; q.alpha.c2 = 0; q.alpha.c3 = 0;
    q.beta.c0  = 0; q.beta.c1  = 0; q.beta.c2  = 0; q.beta.c3  = 0;
    q.k = 0;

    /* State preparation (from the '@prepare' directive). */


    qstate_t q_ref = q;
    (void)q_ref;

    /* === TRANSLATED QUANTUM LOGIC (from Q#) === */
    q = apply_H_exact(q); check_unitarity_exact(q);
    q = apply_H_exact(q); check_unitarity_exact(q);
    /* === END OF TRANSLATED QUANTUM LOGIC === */

    /* === PROPERTY UNDER VERIFICATION === */
    __ESBMC_assert(state_eq_exact(q, q_ref),
                   "exact functional equivalence failed");

    return 0;
}
