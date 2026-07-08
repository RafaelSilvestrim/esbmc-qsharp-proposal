// Experiment 4 — deliberate fault: S.S is asserted to be the identity on
// |1>, but S^2 = Z introduces a phase flip (-|1>). ESBMC must return SAT
// (violated) with a counterexample exposing the divergent amplitude.
// The X preparation runs before the reference snapshot (@prepare), so the
// harness compares the final state against |1>, not |0>.
// @prepare: X
// @property: identity
namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestSIdentity() : Unit {
        use q = Qubit();

        S(q);
        S(q);
    }
}
