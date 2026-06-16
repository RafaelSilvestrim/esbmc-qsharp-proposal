#!/usr/bin/env python3
"""
qsharp2c.py  —  Tradutor Inteligente (Suporta 1 e 2 Qubits dinamicamente)
"""

import sys
import re
import os
import pathlib

def translate_qsharp_to_c(source: str):
    c_lines = []
    in_test_op = False
    qubits_count = 1
    finished = False  # Flag de parada total
    
    for line in source.split('\n'):
        stripped = line.strip()
        if not stripped: continue
            
        if stripped.startswith("operation "):
            in_test_op = True
            continue
            
        if in_test_op:
            # PARADA TOTAL: Se encontrar medição, reset ou final de bloco, encerra a tradução
            if any(cmd in stripped for cmd in ["M(", "Measure", "Reset", "r =="]):
                finished = True
            
            if finished: continue 

            # Identifica número de qubits
            if "Qubit()" in stripped and "," in stripped:
                qubits_count = 2
            elif "Qubit()" in stripped and qubits_count == 1:
                pass # mantém 1
                
            # Tradução de portas
            if re.match(r'X\s*\(.*\)\s*;', stripped):
                c_lines.append("  q = apply_X(q); check_stability(q);")
            
            elif re.match(r'H\s*\(.*\)\s*;', stripped):
                if qubits_count == 2:
                    # H no primeiro qubit de um sistema de 2 qubits
                    c_lines.append("  s = apply_H_2q(s); check_stability_2q(s);")
                else:
                    c_lines.append("  q = apply_H(q); check_stability(q);")
            
            elif re.match(r'CNOT\s*\(.*\)\s*;', stripped):
                c_lines.append("  s = apply_CNOT(s); check_stability_2q(s);")

            elif re.match(r'S\s*\(.*\)\s*;', stripped):
                c_lines.append("  q = apply_S(q); check_stability(q);")

    return "\n".join(c_lines), qubits_count

def render_c(ops_c: str, num_qubits: int) -> str:
    # Escolhe o template C fisicamente correto para a quantidade de Qubits
    tpl_name = "C_HARNESS_TEMPLATE_2Q.c" if num_qubits == 2 else "C_HARNESS_TEMPLATE_1Q.c"
    tpl_path = pathlib.Path(__file__).parent / "templates" / tpl_name
    template = tpl_path.read_text(encoding="utf-8")
    
    # Injeta o código
    c = template.replace("/* <INJECT_LOGIC> */", ops_c)
    # Suporte legado para a tag antiga caso ainda exista
    c = c.replace("/* {{OPERACOES_EM_C}} */", ops_c)
    return c

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 translator/qsharp2c.py <input.qs> <output.c>")
        sys.exit(2)

    inp, out = sys.argv[1], sys.argv[2]

    with open(inp, encoding="utf-8") as f:
        src = f.read()

    ops_c, num_qubits = translate_qsharp_to_c(src)
    c_code = render_c(ops_c, num_qubits)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(c_code)
        
    print(f"[ok] Gerado: {out} (usando molde de {num_qubits} Qubit(s))")

if __name__ == "__main__":
    main()