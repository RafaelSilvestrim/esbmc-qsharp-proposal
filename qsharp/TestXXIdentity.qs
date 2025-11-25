namespace ESBMCQSharpDemo {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;

    operation PrepareQubit(initial : Result, q : Qubit) : Unit is Adj + Ctl {
        if (initial == One) {
            X(q);
        }
    }

    operation TestXXIdentity(initial : Result) : Unit {
        use q = Qubit();
        PrepareQubit(initial, q);

        
        X(q);
        X(q);
        

        let r = M(q);
        if (r != initial) {
            fail $"Violação: X∘X != I para initial = {initial}";
        }

        if (r == One) {
            X(q); // reset
        }
    }

    @EntryPoint()
    operation Main() : Unit {
        TestXXIdentity(Zero);
        TestXXIdentity(One);
    }
}
