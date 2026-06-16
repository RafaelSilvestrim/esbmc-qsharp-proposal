namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestSIdentity() : Unit {
        use q = Qubit();
        X(q); // Agora começamos em |1>
        S(q);
        S(q);
        // S^2 no estado |1> deve resultar em -|1>
        // O nosso verificador de identidade vai ver -1.0 != 1.0 e vai FALHAR!
    }
}