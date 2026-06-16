namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;

    operation PrepareQubit(initial : Result, q : Qubit) : Unit is Adj + Ctl {
        if (initial == One) {
            X(q);
        }
    }

    // operation TestXXIdentity(initial : Result) : Unit {
    //     use q = Qubit();
    //     PrepareQubit(initial, q);

        
    //     X(q);
    //     X(q);
        

    //     let r = M(q);
    //     if (r != initial) {
    //         fail $"Violação: X∘X != I para initial = {initial}";
    //     }

    //     if (r == One) {
    //         X(q); // reset
    //     }
    // }

    operation TestXXIdentity(initial : Result) : Unit {
        use q = Qubit();
        // Prepara o qubit no estado inicial (0 ou 1)
        PrepareQubit(initial, q); 
        
        // Aplicação da Identidade: X o X = I
        X(q); 
        X(q);
        
        // Se a medição falhar em retornar ao estado inicial, gera erro
        if (M(q) != initial) {
            fail "Violation of Unitary Identity";
        }
    }

    @EntryPoint()
    operation Main() : Unit {
        TestXXIdentity(Zero);
        TestXXIdentity(One);
    }
}
