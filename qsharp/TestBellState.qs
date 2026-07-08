// Experiment 3 — Bell state preparation: (H x I) then CNOT on |00>.
// The injected property asserts the target amplitudes of (|00>+|11>)/sqrt(2).
// @property: bell
namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestBellState() : Unit {
        use (q1, q2) = (Qubit(), Qubit());

        H(q1);
        CNOT(q1, q2);
    }
}
