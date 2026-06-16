namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Intrinsic;

    operation TestXXIdentity() : Unit {
        use q = Qubit();
        // O estado inicial |0> já é fixo no nosso template C.
        // Basta aplicar a identidade.
        X(q); 
        X(q);
        
        // Medição e fim do teste lógico
        let r = M(q);
    }
}