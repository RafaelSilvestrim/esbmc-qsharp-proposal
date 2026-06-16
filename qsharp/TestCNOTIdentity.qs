namespace QuantumFormalVerification {
    open Microsoft.Quantum.Intrinsic;

    operation TestCNOTIdentity() : Unit {
        // Aloca 2 qubits
        use (q1, q2) = (Qubit(), Qubit());
        
        // CNOT * CNOT = I
        CNOT(q1, q2);
        CNOT(q1, q2);
    }
}