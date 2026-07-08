// Experiment 2b — CNOT unitarity: CNOT.CNOT = I on |00>.
// @property: identity
namespace QuantumFormalVerification {
    open Microsoft.Quantum.Intrinsic;

    operation TestCNOTIdentity() : Unit {
        use (q1, q2) = (Qubit(), Qubit());

        CNOT(q1, q2);
        CNOT(q1, q2);
    }
}
