namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestBellState() : Unit {
        use (q1, q2) = (Qubit(), Qubit());
        
        // Criar Bell State: H + CNOT
        H(q1);
        CNOT(q1, q2);
        
        // Verificação: O estado final esperado tem amplitudes 1/sqrt(2) em 00 e 11
        // (O nosso molde em C já tem a verificação de unitariedade/estabilidade)
    }
}