# Q# – Teste de Identidade (X∘X = I)

## Como rodar localmente (SDK .NET + QDK)
1. Instale o .NET SDK (6.0+).
2. Instale o Quantum Development Kit (`dotnet new -i Microsoft.Quantum.ProjectTemplates`).
3. Crie um projeto Q#:
   ```bash
   dotnet new console -lang Q#
   ```
4. Substitua o conteúdo de `Program.qs` (ou `*.qs` gerado) por `TestXXIdentity.qs` deste diretório.
5. Rode:
   ```bash
   dotnet run
   ```

**O que o teste faz?**  
- Prepara |0⟩ e |1⟩; aplica `X` duas vezes e mede em Z.  
- Em ambos os casos, o resultado após `X∘X` deve ser o mesmo bit inicial.
