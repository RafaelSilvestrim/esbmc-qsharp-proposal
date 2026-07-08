// Experiment 6 — non-Clifford sequence: H;T;T must be equivalent to H;S,
// since T^2 = S. Verified in both encodings:
//   float: esbmc <c> --unwind 1 --z3 --floatbv   (tolerance-based)
//   exact: esbmc <c> --unwind 16 --z3            (zero-tolerance, Z[w] ring)
// @property: equiv_hs
namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestTGate() : Unit {
        use q = Qubit();

        H(q);
        T(q);
        T(q);
    }
}
