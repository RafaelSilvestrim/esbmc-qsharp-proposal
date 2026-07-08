// Experiment 5 — QRNG validation artifact (PQC-supporting).
// A quantum random number generator used for key-material generation must
// produce an unbiased bit: after H|0>, both measurement outcomes must have
// probability exactly 1/2. The injected property asserts this uniformity
// before the measurement.
// @property: uniform
namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation SampleRandomBit() : Result {
        use q = Qubit();

        H(q);

        return M(q);
    }
}
