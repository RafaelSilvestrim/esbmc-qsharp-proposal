import re
import sys
import os

class QSharpToCHarness:
    def __init__(self):
        # Cabeçalho do Harness C com suporte a amplitudes complexas e estabilidade
        self.c_template_header = """
#include <stdio.h>
#include <stdbool.h>
#include <math.h>

// Estruturas para o Modelo Intermediário (Intermediate Model)
typedef struct { double real; double imag; } complex_t;
typedef struct { complex_t alpha; complex_t beta; } qubit_t;

// Propriedade Φ: Verificador de Estabilidade Numérica (Overflow/Underflow)
void check_stability(qubit_t q) {
    double norm_sq = (q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag) +
                     (q.beta.real * q.beta.real + q.beta.imag * q.beta.imag);
    
    // Verifica se a precisão digital manteve a unitariedade física
    __ESBMC_assert(norm_sq >= 0.999 && norm_sq <= 1.001, "ERRO: Instabilidade Numérica detectada");
}

// Implementação dos Operadores Unitários (Transições T)
qubit_t apply_X(qubit_t q) {
    qubit_t res = { q.beta, q.alpha }; 
    return res;
}

// Expansão futura para o Grupo de Clifford (Sprint 3)
// qubit_t apply_H(qubit_t q) { ... }

int main() {
    // Inicialização Simbólica (Exploração exaustiva k=1)
    qubit_t q;
    q.alpha.real = __VERIFIER_nondet_double();
    q.alpha.imag = 0.0;
    q.beta.real = __VERIFIER_nondet_double();
    q.beta.imag = 0.0;

    // Pré-condição: Estado deve ser fisicamente admissível
    double init_norm = (q.alpha.real * q.alpha.real) + (q.beta.real * q.beta.real);
    __ESBMC_assume(init_norm >= 0.999 && init_norm <= 1.001);
    
    complex_t initial_state = q.alpha;
"""
        self.c_template_footer = """
    return 0;
}
"""

    def translate(self, qsharp_code):
        c_body = ""
        # Regex simples para identificar o subconjunto determinístico atual {X, fail} [1]
        lines = qsharp_code.split('\\n')
        for line in lines:
            line = line.strip()
            
            # Mapeamento da Porta Pauli-X com injeção de estabilidade
            if re.match(r'X\\(.*?\\);', line):
                c_body += "    q = apply_X(q);\\n"
                c_body += "    check_stability(q); // Propriedade de Estabilidade Numérica\\n"
            
            # Mapeamento do Fallback/Fail para Asserção Formal
            elif "fail" in line:
                error_msg = re.search(r'fail "(.*?)";', line)
                msg = error_msg.group(1) if error_msg else "Violation"
                c_body += f'    __ESBMC_assert(false, "{msg}");\\n'
                
            # Mapeamento de Identidade (Check final de reversibilidade)
            elif "M(q) != initial" in line or "Quantum identity violated" in line:
                c_body += "    __ESBMC_assert(q.alpha.real == initial_state.real, \"Quantum identity violated\");\\n"

        return self.c_template_header + c_body + self.c_template_footer

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 qsharp2c.py <input.qs> <output.c>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Erro: Arquivo {input_file} não encontrado.")
        return

    with open(input_file, 'r') as f:
        qsharp_code = f.read()

    translator = QSharpToCHarness()
    c_code = translator.translate(qsharp_code)

    with open(output_file, 'w') as f:
        f.write(c_code)

    print(f"Sucesso! Intermediate Model gerado em: {output_file}")

if __name__ == "__main__":
    main()