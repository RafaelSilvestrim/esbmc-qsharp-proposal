#!/usr/bin/env python3
"""
vbe_gate.py — pre-execution technology gate (stages E2 -> E3 -> E4).

Runs the complete VBE flow for one Q# artifact and maps the verification
verdict to a governance decision through the process exit code, so the
script can be dropped into any CI/CD pipeline (GitLab CI, Jenkins, GitHub
Actions) as a blocking step:

  UNSAT   -> PROMOTE  (exit 0)  artifact may advance in the lifecycle
  SAT     -> BLOCK    (exit 1)  counterexample archived in the risk register
  TIMEOUT -> ESCALATE (exit 2)  manual review; increase k or decompose

Every run emits a signed JSON-LD evidence record under results/evidence/.

Usage:
  python3 governance/vbe_gate.py <circuit.qs>
      [--encoding float|exact] [--property P] [--timeout SECONDS]
      [--out-dir results/evidence] [--build-dir build] [--quiet]
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "translator"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import qsharp2c      # noqa: E402
import sign_record   # noqa: E402

ESBMC_BIN = os.environ.get("ESBMC", "esbmc")

EXIT_CODES = {"UNSAT": 0, "SAT": 1, "TIMEOUT": 2, "ERROR": 2}
DECISIONS = {
    "UNSAT": "PROMOTE",
    "SAT": "BLOCK",
    "TIMEOUT": "ESCALATE_MANUAL_REVIEW",
    "ERROR": "ESCALATE_MANUAL_REVIEW",
}

RE_VCCS = re.compile(r"Generated (\d+) VCC\(s\), (\d+) remaining")
RE_SOLVER_TIME = re.compile(r"Runtime decision procedure: ([\d.]+)s")
RE_BMC_TIME = re.compile(r"BMC program time: ([\d.]+)s")
RE_SOLVER_NAME = re.compile(r"Solving with solver (.+)")
RE_VIOLATED = re.compile(r"Violated property:.*?(?:\n\n|\Z)", re.DOTALL)


def esbmc_version() -> str:
    try:
        out = subprocess.run([ESBMC_BIN, "--version"], capture_output=True,
                             text=True, timeout=30).stdout
        m = re.search(r"ESBMC version ([\w.\- ]+)", out)
        return m.group(1).strip() if m else out.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def run_esbmc(harness: str, flags: str, timeout: float):
    """Invoke ESBMC on a harness; return a metrics dict."""
    cmd = [ESBMC_BIN, harness] + flags.split()
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
        wall = time.monotonic() - started
        out = proc.stdout + proc.stderr
        if "VERIFICATION SUCCESSFUL" in out:
            verdict = "UNSAT"
        elif "VERIFICATION FAILED" in out:
            verdict = "SAT"
        else:
            verdict = "ERROR"
    except subprocess.TimeoutExpired as e:
        wall = time.monotonic() - started
        out = ((e.stdout or b"").decode(errors="replace") +
               (e.stderr or b"").decode(errors="replace"))
        verdict = "TIMEOUT"

    metrics = {
        "command": " ".join(cmd).replace(str(REPO_ROOT) + os.sep, ""),
        "verdict": verdict,
        "wall_time_s": round(wall, 3),
        "raw_output": out,
    }
    if m := RE_VCCS.search(out):
        metrics["vccs_generated"] = int(m.group(1))
        metrics["vccs_remaining"] = int(m.group(2))
    if m := RE_SOLVER_TIME.search(out):
        metrics["solver_time_s"] = float(m.group(1))
    if m := RE_BMC_TIME.search(out):
        metrics["bmc_time_s"] = float(m.group(1))
    if m := RE_SOLVER_NAME.search(out):
        metrics["solver"] = m.group(1).strip()
    if verdict == "SAT":
        if m := RE_VIOLATED.search(out):
            # Keep the counterexample compact: property block, first lines,
            # with machine-local path prefixes stripped.
            snippet = "\n".join(m.group(0).strip().splitlines()[:6])
            metrics["violated_property"] = snippet.replace(
                str(REPO_ROOT) + os.sep, "")
    return metrics


def build_record(circuit: str, info: dict, metrics: dict) -> dict:
    """Assemble the JSON-LD evidence record for the accountability registry."""
    circuit_id = pathlib.Path(circuit).stem
    record = {
        "@context": "https://w3id.org/security/v2",
        "@type": "VerificationRecord",
        "circuit_id": circuit_id,
        "artifact": os.path.basename(circuit),
        "pipeline": {
            "transpiler": qsharp2c.TRANSPILER_VERSION,
            "verifier": f"ESBMC {esbmc_version()}",
            "solver": metrics.get("solver", "Z3"),
            "flags": info["esbmc_flags"],
        },
        "property": info["property"],
        "amplitude_encoding": info["encoding"],
        "qubits": info["qubits"],
        "circuit_depth": info["depth"],
        "bound_k": info["bound_k"],
        "verdict": metrics["verdict"],
        "governance_decision": DECISIONS[metrics["verdict"]],
        "metrics": {
            "vccs": metrics.get("vccs_generated"),
            "solver_time_s": metrics.get("solver_time_s"),
            "bmc_time_s": metrics.get("bmc_time_s"),
            "wall_time_s": metrics["wall_time_s"],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if "violated_property" in metrics:
        record["counterexample"] = metrics["violated_property"]
    return record


def run_gate(circuit: str, encoding=None, prop=None, timeout=300.0,
             out_dir="results/evidence", build_dir="build", quiet=False):
    """Full E2->E4 flow for one circuit. Returns (record, exit_code)."""
    circuit_id = pathlib.Path(circuit).stem
    suffix = f"_{encoding}" if encoding else ""
    harness = str(pathlib.Path(build_dir) / f"{circuit_id}{suffix}.c")

    info = qsharp2c.transpile(circuit, harness, encoding=encoding,
                              prop=prop, quiet=True)
    metrics = run_esbmc(harness, info["esbmc_flags"], timeout)
    record = build_record(circuit, info, metrics)
    signed = sign_record.sign_record(record)

    out_path = pathlib.Path(out_dir) / f"{circuit_id}{suffix}.jsonld"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(signed, f, indent=2, ensure_ascii=False)
        f.write("\n")

    code = EXIT_CODES[metrics["verdict"]]
    if not quiet:
        print(f"[{metrics['verdict']}] {circuit_id} "
              f"(encoding={info['encoding']}, property={info['property']}, "
              f"k={info['bound_k']}) -> {record['governance_decision']}")
        print(f"     evidence: {out_path}")
    # Attach runtime extras for callers (not part of the signed record).
    signed["_metrics"] = metrics
    signed["_info"] = info
    return signed, code


def main():
    ap = argparse.ArgumentParser(description="VBE pre-execution gate")
    ap.add_argument("circuit", help="Q# source file (.qs)")
    ap.add_argument("--encoding", choices=["float", "exact"])
    ap.add_argument("--property", dest="prop")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--out-dir", default="results/evidence")
    ap.add_argument("--build-dir", default="build")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    try:
        _, code = run_gate(args.circuit, args.encoding, args.prop,
                           args.timeout, args.out_dir, args.build_dir,
                           args.quiet)
    except qsharp2c.TranspileError as e:
        print(f"[error] transpilation failed: {e}", file=sys.stderr)
        sys.exit(EXIT_CODES["ERROR"])
    sys.exit(code)


if __name__ == "__main__":
    main()
