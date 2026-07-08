#!/usr/bin/env python3
"""
qsharp2c.py — Q# -> C transpiler for the ESBMC-Q# VBE (Verify Before
Execution) pipeline.

Stage E2 of the pipeline: reads a restricted Q# program (Clifford+T gates
over 1 or 2 qubits, straight-line, measurement-terminated), extracts the
unitary region, and instantiates a C verification harness in which every
gate is a fixed, manually reviewed linear transformation over the state
amplitudes. Property assertions are injected so ESBMC can decide them
exhaustively up to the bound k.

Two amplitude encodings are supported (Section IV of the paper):

  float  — IEEE 754 doubles (verify with: esbmc <c> --unwind 1 --z3 --floatbv).
           Models the arithmetic actually executed by classical control
           software; used for numerical-stability invariants. Assertions
           carry explicit tolerances.
  exact  — exact rational encoding over the ring Z[w]/sqrt(2)^k, w = e^{i pi/4}
           (verify with: esbmc <c> --unwind 16 --z3). Integer-only, no
           tolerances; used for algebraic properties (unitarity, functional
           equivalence) of Clifford+T operators. 1-qubit circuits only.

Q# source directives (comments interpreted by the transpiler):

  // @property: identity | uniform | bell | equiv_hs | stability
  // @prepare:  X                (gates applied before the reference snapshot)
  // @encoding: float | exact    (default: float; overridden by --encoding)

Usage:
  python3 translator/qsharp2c.py <input.qs> <output.c>
      [--property P] [--encoding E] [--quiet]
"""

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

TRANSPILER_VERSION = "qsharp2c.py v2.0"

# Recommended ESBMC invocation per encoding (recorded in the governance
# manifest so stage E3 is reproducible from the E2 evidence alone).
ESBMC_FLAGS = {
    "float": "--unwind 1 --z3 --floatbv",
    "exact": "--unwind 16 --z3",
}

TEMPLATES = {
    ("float", 1): "harness_1q_float.c",
    ("float", 2): "harness_2q_float.c",
    ("exact", 1): "harness_1q_exact.c",
}

# --------------------------------------------------------------------------
# Gate emission tables: Q# gate -> C statement per (encoding, qubit count).
# q_idx is the 0-based index of the qubit operand within the 'use' binding.
# --------------------------------------------------------------------------

def emit_gate_1q_float(gate: str) -> str:
    return f"    q = apply_{gate}(q); check_stability(q);"

def emit_gate_1q_exact(gate: str) -> str:
    return f"    q = apply_{gate}_exact(q); check_unitarity_exact(q);"

def emit_gate_2q_float(gate: str, q_idx: int) -> str:
    return f"    s = apply_{gate}_q{q_idx + 1}(s); check_stability_2q(s);"

SUPPORTED_1Q_GATES = {"X", "H", "S", "T", "Z"}
SUPPORTED_2Q_SINGLE_GATES = {"X", "H"}  # single-qubit gates available in C^4

# Human-readable property names for the governance manifest.
PROPERTY_LABELS = {
    "identity":  "Functional equivalence (final state = reference state)",
    "uniform":   "QRNG uniformity (P(0) = P(1) = 1/2)",
    "bell":      "Bell fidelity (target amplitudes of (|00>+|11>)/sqrt(2))",
    "equiv_hs":  "Non-Clifford equivalence (H.T.T = H.S on |0>)",
    "stability": "Numerical stability / norm preservation only",
}

# --------------------------------------------------------------------------
# Property assertion snippets injected at /* <INJECT_PROPERTY> */.
# --------------------------------------------------------------------------

PROPERTY_SNIPPETS = {
    ("float", 1, "identity"): """\
    /* Component-wise assertions so a counterexample names the divergent
     * amplitude (e.g. a phase flip on |1> violates only the beta check). */
    __ESBMC_assert(close_to(q.alpha.real, q_ref.alpha.real) &&
                   close_to(q.alpha.imag, q_ref.alpha.imag),
                   "functional equivalence: alpha (|0>) amplitude diverges");
    __ESBMC_assert(close_to(q.beta.real,  q_ref.beta.real)  &&
                   close_to(q.beta.imag,  q_ref.beta.imag),
                   "functional equivalence: beta (|1>) amplitude diverges");""",
    ("float", 1, "uniform"): """\
    /* QRNG artifact: before measurement the outcome distribution must be
     * uniform, i.e. |alpha|^2 = |beta|^2 = 1/2. */
    double p_zero = q.alpha.real * q.alpha.real + q.alpha.imag * q.alpha.imag;
    double p_one  = q.beta.real  * q.beta.real  + q.beta.imag  * q.beta.imag;
    __ESBMC_assert(close_to(p_zero, 0.5) && close_to(p_one, 0.5),
                   "QRNG uniformity: outcomes not equiprobable");""",
    ("float", 1, "equiv_hs"): """\
    /* Reference state: (S.H)|0> = (|0> + i|1>)/sqrt(2). Since T.T = S, the
     * translated circuit H;T;T must reach the same state. */
    __ESBMC_assert(close_to(q.alpha.real, INV_SQRT2) && close_to(q.alpha.imag, 0.0) &&
                   close_to(q.beta.real,  0.0)       && close_to(q.beta.imag,  INV_SQRT2),
                   "non-Clifford equivalence T.T = S failed");""",
    ("float", 1, "stability"): """\
    check_stability(q);""",
    ("float", 2, "identity"): """\
    __ESBMC_assert(close_to(s.amp00.real, s_ref.amp00.real) && close_to(s.amp00.imag, s_ref.amp00.imag) &&
                   close_to(s.amp01.real, s_ref.amp01.real) && close_to(s.amp01.imag, s_ref.amp01.imag) &&
                   close_to(s.amp10.real, s_ref.amp10.real) && close_to(s.amp10.imag, s_ref.amp10.imag) &&
                   close_to(s.amp11.real, s_ref.amp11.real) && close_to(s.amp11.imag, s_ref.amp11.imag),
                   "functional equivalence: final state != reference state");""",
    ("float", 2, "bell"): """\
    /* Target entangled state: (|00> + |11>)/sqrt(2). */
    __ESBMC_assert(close_to(s.amp00.real, INV_SQRT2) && close_to(s.amp00.imag, 0.0) &&
                   close_to(s.amp01.real, 0.0)       && close_to(s.amp01.imag, 0.0) &&
                   close_to(s.amp10.real, 0.0)       && close_to(s.amp10.imag, 0.0) &&
                   close_to(s.amp11.real, INV_SQRT2) && close_to(s.amp11.imag, 0.0),
                   "Bell fidelity: amplitudes differ from (|00>+|11>)/sqrt(2)");""",
    ("float", 2, "stability"): """\
    check_stability_2q(s);""",
    ("exact", 1, "identity"): """\
    __ESBMC_assert(state_eq_exact(q, q_ref),
                   "exact functional equivalence failed");""",
    ("exact", 1, "uniform"): """\
    /* Exact uniformity: |alpha|^2 == |beta|^2 as elements of Z[sqrt(2)]. */
    __ESBMC_assert(zw_norm_p0(q.alpha) == zw_norm_p0(q.beta) &&
                   zw_norm_p1(q.alpha) == zw_norm_p1(q.beta),
                   "exact QRNG uniformity failed");""",
    ("exact", 1, "equiv_hs"): """\
    /* Reference state built exactly: (S.H)|0>. */
    qstate_t ref;
    ref.alpha.c0 = 1; ref.alpha.c1 = 0; ref.alpha.c2 = 0; ref.alpha.c3 = 0;
    ref.beta.c0  = 0; ref.beta.c1  = 0; ref.beta.c2  = 0; ref.beta.c3  = 0;
    ref.k = 0;
    ref = apply_H_exact(ref);
    ref = apply_S_exact(ref);
    __ESBMC_assert(state_eq_exact(q, ref),
                   "exact non-Clifford equivalence T.T = S failed");""",
    ("exact", 1, "stability"): """\
    check_unitarity_exact(q);""",
}

# --------------------------------------------------------------------------
# Q# parsing
# --------------------------------------------------------------------------

RE_DIRECTIVE = re.compile(r"//\s*@(property|prepare|encoding):\s*([\w,\s]+)")
RE_USE_ONE   = re.compile(r"use\s+(\w+)\s*=\s*Qubit\(\)")
RE_USE_TWO   = re.compile(r"use\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*=")
RE_GATE_1    = re.compile(r"^(X|H|S|T|Z)\s*\(\s*(\w+)\s*\)\s*;")
RE_CNOT      = re.compile(r"^CNOT\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*;")
# Measurement / reset marks the end of the unitary region we verify.
RE_END_UNITARY = re.compile(r"\bM\s*\(|\bMeasure\b|\bReset\b")


class TranspileError(Exception):
    pass


def parse_qsharp(source: str):
    """Extract (directives, qubit names, gate list) from a restricted Q#
    program. Gates are returned as (name, operand_indices) tuples in program
    order; translation stops at the first measurement or reset."""
    directives = {}
    qubits = []
    gates = []
    in_operation = False
    unitary_region = True

    for raw_line in source.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        m = RE_DIRECTIVE.search(line)
        if m:
            directives[m.group(1)] = m.group(2).strip()
            continue
        if line.startswith("//"):
            continue

        if line.startswith("operation "):
            if in_operation or qubits:
                raise TranspileError(
                    "multiple operations found; the transpiler verifies a "
                    "single entry-point operation per file")
            in_operation = True
            continue
        if not in_operation:
            continue

        m = RE_USE_TWO.search(line)
        if m:
            qubits = [m.group(1), m.group(2)]
            continue
        m = RE_USE_ONE.search(line)
        if m:
            qubits = [m.group(1)]
            continue

        if RE_END_UNITARY.search(line):
            unitary_region = False
        if not unitary_region:
            continue

        m = RE_GATE_1.match(line)
        if m:
            gate, operand = m.group(1), m.group(2)
            if operand not in qubits:
                raise TranspileError(f"gate {gate} applied to undeclared qubit '{operand}'")
            gates.append((gate, [qubits.index(operand)]))
            continue
        m = RE_CNOT.match(line)
        if m:
            ctrl, tgt = m.group(1), m.group(2)
            if [ctrl, tgt] != qubits:
                raise TranspileError(
                    "CNOT is currently supported only as CNOT(q1, q2) with "
                    "q1 = control and q2 = target, in declaration order")
            gates.append(("CNOT", [0, 1]))
            continue

    if not qubits:
        raise TranspileError("no qubit allocation ('use' statement) found")
    return directives, qubits, gates


# --------------------------------------------------------------------------
# C code generation
# --------------------------------------------------------------------------

def emit_ops(gates, encoding: str, num_qubits: int):
    """Translate the parsed gate list into C statements."""
    lines = []
    for gate, operands in gates:
        if num_qubits == 1:
            if gate not in SUPPORTED_1Q_GATES:
                raise TranspileError(f"unsupported 1-qubit gate: {gate}")
            emit = emit_gate_1q_exact if encoding == "exact" else emit_gate_1q_float
            lines.append(emit(gate))
        else:
            if gate == "CNOT":
                lines.append("    s = apply_CNOT(s); check_stability_2q(s);")
            elif gate in SUPPORTED_2Q_SINGLE_GATES:
                lines.append(emit_gate_2q_float(gate, operands[0]))
            else:
                raise TranspileError(f"unsupported gate in C^4: {gate}")
    return lines


def render_harness(directives, num_qubits, gates, encoding, prop) -> str:
    key = (encoding, num_qubits)
    if key not in TEMPLATES:
        raise TranspileError(
            f"no template for encoding '{encoding}' with {num_qubits} qubit(s) "
            "(exact encoding currently supports 1 qubit only)")
    tpl_path = pathlib.Path(__file__).parent / "templates" / TEMPLATES[key]
    template = tpl_path.read_text(encoding="utf-8")

    snippet_key = (encoding, num_qubits, prop)
    if snippet_key not in PROPERTY_SNIPPETS:
        raise TranspileError(
            f"property '{prop}' is not available for {num_qubits} qubit(s) "
            f"with encoding '{encoding}'")

    prepare_gates = []
    if "prepare" in directives:
        for name in directives["prepare"].replace(" ", "").split(","):
            if name:
                prepare_gates.append((name, [0]))
    prepare_lines = emit_ops(prepare_gates, encoding, num_qubits)
    logic_lines = emit_ops(gates, encoding, num_qubits)

    c = template.replace("/* <INJECT_PREPARE> */", "\n".join(prepare_lines))
    c = c.replace("/* <INJECT_LOGIC> */", "\n".join(logic_lines))
    c = c.replace("/* <INJECT_PROPERTY> */", PROPERTY_SNIPPETS[snippet_key])
    return c


# --------------------------------------------------------------------------
# Governance manifest (stage E4 input): one JSON-LD document per transpiled
# artifact, recording what was generated, which properties were injected and
# how the verification engine must be invoked.
# --------------------------------------------------------------------------

def write_governance_manifest(inp_path, out_c_path, num_qubits, depth,
                              encoding, prop, quiet):
    base_name = os.path.splitext(os.path.basename(inp_path))[0]
    log_path = os.path.join(os.path.dirname(out_c_path) or ".",
                            f"{base_name}_governance.json")

    manifest = {
        "@context": "https://schema.org/",
        "@type": "SoftwareSourceCode",
        "artifactName": os.path.basename(inp_path),
        "targetHarness": os.path.basename(out_c_path),
        "transpilerVersion": TRANSPILER_VERSION,
        "quantumConfiguration": {
            "qubitsAllocated": num_qubits,
            "hilbertSpaceDimension": f"C^{2 ** num_qubits}",
            "circuitDepth": depth,
            "boundK": depth + 1,
        },
        "verification": {
            "amplitudeEncoding": encoding,
            "property": prop,
            "propertyDescription": PROPERTY_LABELS[prop],
            "esbmcFlags": ESBMC_FLAGS[encoding],
        },
        "governanceMetadata": {
            "pipelineStage": "E2: Pre-Execution VBE Transpilation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "complianceAction": "PENDING_SMT_VERIFICATION",
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    if not quiet:
        print(f"[ok] governance manifest: {log_path}")
    return log_path


def transpile(inp: str, out: str, encoding=None, prop=None, quiet=False):
    """Programmatic entry point (also used by governance/vbe_gate.py).
    Returns a dict describing the generated artifact."""
    with open(inp, encoding="utf-8") as f:
        src = f.read()

    directives, qubits, gates = parse_qsharp(src)
    num_qubits = len(qubits)

    encoding = encoding or directives.get("encoding", "float")
    if encoding not in ESBMC_FLAGS:
        raise TranspileError(f"unknown encoding '{encoding}'")
    default_prop = "identity" if num_qubits == 1 else "stability"
    prop = prop or directives.get("property", default_prop)

    c_code = render_harness(directives, num_qubits, gates, encoding, prop)

    out_dir = os.path.dirname(out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(c_code)
    if not quiet:
        print(f"[ok] generated: {out} ({num_qubits} qubit(s), encoding={encoding}, "
              f"property={prop}, depth={len(gates)})")

    manifest_path = write_governance_manifest(
        inp, out, num_qubits, len(gates), encoding, prop, quiet)

    return {
        "harness": out,
        "manifest": manifest_path,
        "qubits": num_qubits,
        "depth": len(gates),
        "bound_k": len(gates) + 1,
        "encoding": encoding,
        "property": prop,
        "esbmc_flags": ESBMC_FLAGS[encoding],
    }


def main():
    ap = argparse.ArgumentParser(description="Q# -> C transpiler (VBE stage E2)")
    ap.add_argument("input", help="Q# source file (.qs)")
    ap.add_argument("output", help="C harness to generate (.c)")
    ap.add_argument("--property", dest="prop",
                    choices=sorted(PROPERTY_LABELS.keys()),
                    help="property to inject (overrides the @property directive)")
    ap.add_argument("--encoding", choices=["float", "exact"],
                    help="amplitude encoding (overrides the @encoding directive)")
    ap.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = ap.parse_args()

    try:
        transpile(args.input, args.output, args.encoding, args.prop, args.quiet)
    except TranspileError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
