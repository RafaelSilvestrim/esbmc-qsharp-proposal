namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestTGate() : Unit {
        use q = Qubit();
        H(q); // Coloca em superposição
        T(q); // Aplica a porta Não-Clifford T
        T(q); // Aplica novamente (T * T = S)
    }
}