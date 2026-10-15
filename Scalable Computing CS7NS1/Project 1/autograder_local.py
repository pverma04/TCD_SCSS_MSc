#!/usr/bin/env python3
"""
QIS-NET Project 1 autograder (platform-agnostic core).

Usage:
    python3 grade_project1.py submission.py [--json results.json] [--csv grades.csv]

Deterministic: same code -> same score. Only qiskit/qiskit-aer/numpy required.
Outputs:
  - JSON:  Submitty-style per-testcase results (points awarded / available).
  - CSV:   one-row-per-student Blackboard Grade Centre import line
           (columns: username, p1_score). Username taken from --username or
           the submission filename stem.
"""

import argparse
import importlib.util
import json
import math
import sys
import traceback

import numpy as np

MAX_POINTS = 100


def load_submission(path):
    spec = importlib.util.spec_from_file_location("submission", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- helpers ----------

def statevector_of(circuit):
    from qiskit.quantum_info import Statevector
    return Statevector.from_instruction(circuit)


def fidelity_to_target(sv, target):
    return float(np.abs(np.vdot(target.data, sv.data)) ** 2)


def results_record(testcases):
    total = sum(t["points_awarded"] for t in testcases)
    return {
        "total_points_awarded": total,
        "total_points_available": MAX_POINTS,
        "testcases": testcases,
    }


def tc(name, awarded, available, message=""):
    return {
        "test_name": name,
        "points_awarded": awarded,
        "points_available": available,
        "message": message,
    }


# ---------- task graders ----------

def grade_t1(mod):
    try:
        d = mod.environment_check()
        ok_keys = isinstance(d, dict) and {
            "qiskit_version", "aer_available", "student_id"
        } <= set(d.keys())
        ok_types = (
            isinstance(d.get("qiskit_version"), str)
            and isinstance(d.get("aer_available"), bool)
            and isinstance(d.get("student_id"), str)
            and len(d.get("student_id", "")) > 0
        )
        if ok_keys and ok_types and d["aer_available"]:
            return [tc("T1 environment_check", 10, 10)]
        return [tc("T1 environment_check", 0, 10,
                   f"bad structure/types or aer_available!=True: {d!r}")]
    except Exception:
        return [tc("T1 environment_check", 0, 10, traceback.format_exc(limit=1))]


def grade_t2(mod):
    try:
        qc = mod.bell_state()
        from qiskit import QuantumCircuit
        if not isinstance(qc, QuantumCircuit) or qc.num_qubits != 2:
            return [tc("T2 bell_state", 0, 20, "not a 2-qubit QuantumCircuit")]
        target = np.zeros(4, complex)
        target[0] = target[3] = 1 / math.sqrt(2)
        sv = statevector_of(qc)
        fid = fidelity_to_target(sv, type(sv)(target))
        pts = 20 if fid >= 0.9999 else (10 if fid >= 0.9 else 0)
        return [tc("T2 bell_state", pts, 20, f"fidelity={fid:.6f}")]
    except Exception:
        return [tc("T2 bell_state", 0, 20, traceback.format_exc(limit=1))]


def grade_t3(mod):
    cases = [2, 3, 5, 8]
    per = 3  # 4 x 3 = 12, + 3 for depth check
    out, depth_ok = [], True
    for n in cases:
        try:
            qc = mod.ghz_circuit(n)
            target = np.zeros(2**n, complex)
            target[0] = target[-1] = 1 / math.sqrt(2)
            sv = statevector_of(qc)
            fid = fidelity_to_target(sv, type(sv)(target))
            pts = per if fid >= 0.9999 else 0
            out.append(tc(f"T3 ghz n={n}", pts, per, f"fidelity={fid:.6f}"))
            if qc.depth() > n + 1:
                depth_ok = False
        except Exception:
            out.append(tc(f"T3 ghz n={n}", 0, per, traceback.format_exc(limit=1)))
            depth_ok = False
    out.append(tc("T3 depth bound", 3 if depth_ok else 0, 3))
    return out


def grade_t4(mod):
    from qiskit_aer import AerSimulator
    from qiskit import transpile
    cases = [(0.4, 0.0), (1.1, 0.7), (2.2, 2.9), (2.7, 4.0)]
    sim = AerSimulator(method="statevector", seed_simulator=7)
    out = []
    per_fid, per_struct = 5, 5  # 4x5 fidelity + 5 structural
    struct_ok, struct_msg = True, ""
    for theta, phi in cases:
        try:
            qc = mod.teleport_circuit(theta, phi)
            if qc.num_qubits != 3:
                raise ValueError("circuit must have exactly 3 qubits")
            n_meas = qc.count_ops().get("measure", 0)
            if n_meas < 2:
                struct_ok = False
                struct_msg = f"only {n_meas} measurements"
            qc_save = qc.copy()
            qc_save.save_statevector()
            tqc = transpile(qc_save, sim)
            sv = sim.run(tqc, shots=1).result().get_statevector()
            sv = np.asarray(sv)
            # reduced state of qubit 2 (qubit index 2 = most significant in
            # Qiskit little-endian statevector? q0 is least significant:
            # index = q0 + 2 q1 + 4 q2). Marginalise qubits 0,1.
            amp = sv.reshape(2, 2, 2)  # axes (q2, q1, q0): index = q0 + 2 q1 + 4 q2
            # reduced density matrix of qubit 2: marginalise qubits 0 and 1
            rho2 = np.einsum("aij,bij->ab", amp, amp.conj())
            # expected single-qubit state: circuit applies Ry then Rz, so
            # |psi> = Rz(phi) Ry(theta) |0> = (cos(t/2), e^{i phi} sin(t/2))
            ct, st = math.cos(theta / 2), math.sin(theta / 2)
            phase = np.exp(1j * phi)
            psi = np.array([ct, phase * st])
            fid = float(np.real(np.vdot(psi, rho2 @ psi)))
            pts = per_fid if fid >= 0.9999 else (2 if fid >= 0.95 else 0)
            out.append(tc(f"T4 teleport theta={theta},phi={phi}", pts,
                          per_fid, f"fidelity={fid:.6f}"))
        except Exception:
            struct_ok = False  # no valid circuit -> structural points void
            out.append(tc(f"T4 teleport theta={theta},phi={phi}", 0,
                          per_fid, traceback.format_exc(limit=1)))
    out.append(tc("T4 structural checks", per_struct if struct_ok else 0,
                  per_struct, struct_msg))
    return out


def grade_t5(mod):
    out = []
    shots = 20000
    for p in [0.01, 0.05, 0.1, 0.2]:
        try:
            val = float(mod.repetition_logical_error_rate(p, shots))
            theory = 3 * p**2 * (1 - p) + p**3
            se = math.sqrt(max(theory * (1 - theory), 1e-9) / shots)
            tol = 3 * se + 0.002
            ok = abs(val - theory) <= tol
            pts = 4 if ok else 0
            out.append(tc(f"T5 repetition p={p}", pts, 4,
                          f"value={val:.5f} theory={theory:.5f} tol={tol:.5f}"))
        except Exception:
            out.append(tc(f"T5 repetition p={p}", 0, 4,
                          traceback.format_exc(limit=1)))
    try:
        val = float(mod.repetition_logical_error_rate(0.5, shots))
        ok = abs(val - 0.5) <= 0.03
        out.append(tc("T5 edge p=0.5", 4 if ok else 0, 4,
                      f"value={val:.5f}, expected 0.5 +/- 0.03"))
    except Exception:
        out.append(tc("T5 edge p=0.5", 0, 4, traceback.format_exc(limit=1)))
    return out


def grade_t6(mod):
    try:
        qc = mod.design_challenge()
        if qc.num_qubits != 3:
            return [tc("T6 design_challenge", 0, 10, "must be 3 qubits")]
        if qc.count_ops().get("measure", 0) > 0:
            return [tc("T6 design_challenge", 0, 10, "measurements forbidden")]
        size = qc.size()
        target = np.zeros(8, complex)
        for idx in (1, 2, 4):  # |001>, |010>, |100> in little-endian ints
            target[idx] = 1 / math.sqrt(3)
        sv = statevector_of(qc)
        fid = fidelity_to_target(sv, type(sv)(target))
        if fid >= 0.999 and size <= 8:
            pts = 10
        elif fid >= 0.999:
            pts = 4
        elif fid >= 0.9 and size <= 8:
            pts = 2
        else:
            pts = 0
        return [tc("T6 design_challenge", pts, 10,
                   f"fidelity={fid:.6f} size={size}")]
    except Exception:
        return [tc("T6 design_challenge", 0, 10, traceback.format_exc(limit=1))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("submission")
    ap.add_argument("--json", default="results.json")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--username", default=None)
    args = ap.parse_args()

    mod = load_submission(args.submission)
    testcases = []
    testcases += grade_t1(mod)
    testcases += grade_t2(mod)
    testcases += grade_t3(mod)
    testcases += grade_t4(mod)
    testcases += grade_t5(mod)
    testcases += grade_t6(mod)

    results = results_record(testcases)
    with open(args.json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"TOTAL: {results['total_points_awarded']} / {MAX_POINTS}")
    for t in testcases:
        print(f"  [{t['points_awarded']:>2}/{t['points_available']:>2}] "
              #f"{t['test_name']}  {t['message'][:90]}")
              f"{t['test_name']}  {t['message']}")

    if args.csv:
        username = args.username or args.submission.rsplit("/", 1)[-1].split(".")[0]
        with open(args.csv, "w") as f:
            f.write("username,p1_score\n")
            f.write(f"{username},{results['total_points_awarded']}\n")


if __name__ == "__main__":
    main()
