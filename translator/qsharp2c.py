#!/usr/bin/env python3
"""
qsharp2c.py  —  Protótipo de tradutor Q# -> C simbólico para ESBMC (v0.3 - Complex Amplitudes).

Melhorias:
- Traduz portas X para operadores de matriz complexa (apply_X).
- Injeta verificações de estabilidade numérica automaticamente (check_stability).
"""

import sys
import re
import os
import pathlib

def translate_qsharp_to_c(source: str) -> str:
    """Traduz operações básicas do Q# para sintaxe complexa em C."""
    c_lines = []
    
    # Flags de controle de escopo do parser simplificado
    in_test_op = False
    qubit_name = "q" # Padrão
    
    lines = source.split('\n')
    for line in lines:
        stripped = line.strip()
        
        # Ignora linhas vazias
        if not stripped: continue
            
        # Detecta a operação principal de teste
        if stripped.startswith("operation TestXXIdentity"):
            in_test_op = True
            continue
            
        # Se saiu da operação, para de traduzir o bloco principal
        if in_test_op and stripped == "}":
            # Heurística simples: se achou o fecha-chaves principal (não de um if)
            if len(line) - len(line.lstrip()) == 4: # indentação base
                in_test_op = False
                
        if in_test_op:
            # Detecta declaração de qubit
            match_use = re.match(r'use\s+([a-zA-Z0-9_]+)\s*=\s*Qubit\(\)\s*;', stripped)
            if match_use:
                qubit_name = match_use.group(1)
                # A declaração e o estado inicial |0> já estão fixados no novo template C
                continue
                
            # Traduz preparo do qubit
            if stripped.startswith("PrepareQubit("):
                c_lines.append(f"  // PrepareQubit ignorado: assumindo estado puro |0> fixado no template")
                continue
                
            # Traduz porta X para o domínio contínuo: apply_X(q);
            match_x = re.match(fr'X\s*\(\s*{qubit_name}\s*\)\s*;', stripped)
            if match_x:
                c_lines.append(f"  {qubit_name} = apply_X({qubit_name});")
                c_lines.append(f"  check_stability({qubit_name}); // Verifica a física")
                continue
                
            # Traduz reset final/medição
            if "r == One" in stripped or "M(q)" in stripped or "// reset" in stripped:
                c_lines.append(f"  // Reset ignorado na validação do estado atual")
    
    return "\n".join(c_lines)


def render_c(ops_c: str) -> str:
    tpl_path = pathlib.Path(__file__).parent / "templates" / "C_HARNESS_TEMPLATE.c"
    template = tpl_path.read_text(encoding="utf-8")

    # Substitui a tag no template pelo código C traduzido (suporta ambas as tags)
    c = template.replace("/* {{OPERACOES_EM_C}} */", ops_c)
    c = c.replace("/* <INJECT_LOGIC> */", ops_c)
    return c


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 translator/qsharp2c.py <input.qs> <output.c>")
        sys.exit(2)

    inp, out = sys.argv[1], sys.argv[2]

    with open(inp, encoding="utf-8") as f:
        src = f.read()

    print(f"Traduzindo operações de {inp} para domínio complexo...")
    ops_c = translate_qsharp_to_c(src)
    
    if not ops_c:
        print("Aviso: não encontrei operações compatíveis no arquivo Q#. Gerando harness vazio.")
    
    c_code = render_c(ops_c)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(c_code)

    print(f"[ok] Gerado: {out}")


if __name__ == "__main__":
    main()