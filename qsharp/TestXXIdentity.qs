// Experiment 1 — identity X.X = I on |0>.
// @property: identity
namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestXXIdentity() : Unit {
        use q = Qubit();

        X(q);
        X(q);

        let r = M(q);
    }
}
