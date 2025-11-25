#!/usr/bin/env python3
"""
qsharp2c.py  —  Protótipo mínimo (MVP) de tradutor Q# -> C simbólico para ESBMC.

Nova versão simplificada:
- NÃO depende mais de comentários especiais "Região traduzível".
- Conta todas as ocorrências de `X(q);` no arquivo .qs.
- Gera um harness C que aplica a mesma quantidade de toggles em um bool.

Uso:
  python3 translator/qsharp2c.py qsharp/TestXXIdentity.qs build/generated_toggle.c
  esbmc build/generated_toggle.c --unwind 1
"""

import sys
import re
import os
import pathlib


def count_x_ops(source: str) -> int:
    # Conta linhas que tenham "X(q);" (com espaços opcionais)
    pattern = r'^\s*X\s*\(\s*q\s*\)\s*;'
    return len(re.findall(pattern, source, flags=re.M))


def render_c(num_ops: int) -> str:
    tpl_path = pathlib.Path(__file__).parent / "templates" / "C_HARNESS_TEMPLATE.c"
    template = tpl_path.read_text(encoding="utf-8")

    # Gera N linhas "q = !q;"
    ops_c = "\n  ".join(["q = !q;" for _ in range(num_ops)])

    c = template.replace(
        "/* {{OPERACOES_EM_C}} */",
        "_Bool __INITIAL_Q__ = q;\n  " + ops_c,
    )

    return c


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 translator/qsharp2c.py <input.qs> <output.c>")
        sys.exit(2)

    inp, out = sys.argv[1], sys.argv[2]

    with open(inp, encoding="utf-8") as f:
        src = f.read()

    n_x = count_x_ops(src)
    if n_x == 0:
        print("Aviso: não encontrei nenhuma linha 'X(q);' no arquivo Q#. Gerando harness vazio.")
    else:
        print(f"Encontradas {n_x} ocorrências de X(q);")

    c_code = render_c(n_x)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(c_code)

    print(f"[ok] Gerado: {out}")


if __name__ == "__main__":
    main()
