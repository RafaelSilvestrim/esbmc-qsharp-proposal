// Experiment 2a — identity H.H = I on |0>.
// @property: identity
namespace QuantumFormalVerification {
    open Microsoft.Quantum.Intrinsic;

    operation TestHHIdentity() : Unit {
        use q = Qubit();

        H(q);
        H(q);

        let r = M(q);
    }
}
