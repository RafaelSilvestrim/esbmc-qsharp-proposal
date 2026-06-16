namespace QuantumFormalVerification {
    open Microsoft.Quantum.Intrinsic;

    operation TestHHIdentity() : Unit {
        use q = Qubit();
        
        // H * H = I
        H(q);
        H(q);
        
        // r = M(q); reset q;
    }
}