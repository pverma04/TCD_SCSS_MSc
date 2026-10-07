import qiskit
from qiskit import QuantumCircuit

STUDENT_ID = '26356239'

# T1
# Return a dict with keys `"qiskit_version"` (string), 
# `"aer_available"` (bool, True if `qiskit_aer` imports), 
# and `"student_id"` (string, your university ID).
def environment_check() -> dict:
    # aer available if qiskit imports 
    try:
        import qiskit_aer
        aer_available = True
    except ImportError:
        aer_available = False
    
    return {
        #key value pairs
        "qiskit_version": str(qiskit.__version__),
        "aer_available": aer_available,
        "student_id": STUDENT_ID
    }

#T2
# Return a circuit on 2 qubits (no measurements) whose statevector is 
# $|\Phi^+\rangle = \frac{1}{\sqrt2}(|00\rangle+|11\rangle)$ 
# up to global phase.
def bell_state() -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0) #hadamard to qubit 0
    qc.cx(0, 1) #CNOT. first is control, second is target
    return qc

#T3
# Return an n-qubit circuit (2 ≤ n ≤ 8, no measurements) preparing 
# $\frac{1}{\sqrt2}(|0\rangle^{\otimes n}+|1\rangle^{\otimes n})$.
def ghz_circuit(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(1, n):
        qc.cx(0, i)
    return qc
