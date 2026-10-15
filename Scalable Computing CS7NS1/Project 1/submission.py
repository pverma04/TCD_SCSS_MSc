#AI was used to understand tasks 5 and 6. 
# Only to understand requirments and find sources to understand implementation further. 
# Code is written by me.

from ast import Return
import qiskit
from qiskit import QuantumCircuit
import math


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

# T3
# Return an n-qubit circuit (2 ≤ n ≤ 8, no measurements) preparing 
# $\frac{1}{\sqrt2}(|0\rangle^{\otimes n}+|1\rangle^{\otimes n})$.
def ghz_circuit(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n)
    qc.h(0) #superposition of qubit 0
    for i in range(n - 1):
        qc.cx(i, i + 1) #control i, target i+1
    return qc

# T4
# Return a 3-qubit circuit with 2 classical bits that teleports the state 
# $|\psi\rangle = R_z(\phi)R_y(\theta)|0\rangle$ to qubit 2 — i.e. 
# prepare qubit 0 by applying `ry(theta, 0)` **then** `rz(phi, 0)`:
# qubits 1–2 begin as an ebit you create with H + CNOT;
# perform the Bell-basis operations on qubits 0–1, measure them into the classical bits;
# apply classically-conditioned X and Z corrections on qubit 2;
# **no further gates after the final measurement except the conditioned corrections**.

def teleport_circuit(theta: float, phi: float) -> QuantumCircuit:
    qc = QuantumCircuit(3, 2)

    #prepare |ψ⟩ on qubit 0
    qc.ry(theta, 0)
    qc.rz(phi, 0)
    
    #ebit on qubits 1 and 2
    qc.h(1)
    qc.cx(1, 2)
    
    #bell-basis operations on qubits 0 and 1, measure
    qc.cx(0, 1)
    qc.h(0)
    qc.measure([0, 1], [0, 1])
    
    #apply classically-conditioned corrections on qubit 2
    with qc.if_test((qc.clbits[1], 1)): #x if first bit is 1
        qc.x(2)
    with qc.if_test((qc.clbits[0], 1)): #z if second bit is 1
        qc.z(2)
     
    return qc

# T5
#Using `qiskit_aer` with a **bit-flip (X) error model** 
# applied to every qubit after the encoding (probability `p_phys`), 
# simulate the 3-qubit bit-flip code protecting logical $|0\rangle$: 
# encode (2 CNOTs), apply noise, decode with majority-vote syndrome measurement and correction, 
# and return the **logical error rate** 
# (fraction of shots where the final decoded logical value is 1). 
# Use a seeded simulator (`seed_simulator=42`) and the `shots` argument as the shot count.
def repetition_logical_error_rate(p_phys: float, shots: int) -> float:
    #imports inside to avoid missing import crashing in autograder
    from qiskit_aer import AerSimulator
    from qiskit import QuantumRegister, ClassicalRegister, transpile
    from qiskit_aer.noise import NoiseModel, pauli_error

    data = QuantumRegister(3, "data")
    anc = QuantumRegister(2, "anc")
    syn = ClassicalRegister(2, "syn")
    out = ClassicalRegister(1, "out")
    qc = QuantumCircuit(data, anc, syn, out)

    #logic |0>
    qc.cx(data[0], data[1])
    qc.cx(data[0], data[2])
    qc.barrier()

    #noise
    for i in range(3):
        qc.id(data[i])
    qc.barrier()

    #syndrome extraction
    qc.cx(data[0], anc[0])
    qc.cx(data[1], anc[0])
    qc.cx(data[1], anc[1])
    qc.cx(data[2], anc[1])
    qc.measure(anc[0], syn[0])
    qc.measure(anc[1], syn[1])

    #correction (syn value = s0 + 2*s1)
    #s0=1, s1=0 -> q0 flipped
    with qc.if_test((syn, 1)):   
        qc.x(data[0])
    #s0=1, s1=1 -> q1 flipped
    with qc.if_test((syn, 3)):   
        qc.x(data[1])
    #s0=0, s1=1 -> q2 flipped
    with qc.if_test((syn, 2)):   
        qc.x(data[2])

    #read logic val
    qc.measure(data[0], out[0])

    #noise model: bit flip, prob p_phys on ID gate
    nm = NoiseModel()
    error = pauli_error([('X', p_phys), ('I', 1 - p_phys)])
    nm.add_all_qubit_quantum_error(error, ['id'])
    sim = AerSimulator(noise_model=nm, seed_simulator=42)
    tqc = transpile(qc, sim, optimization_level=0)
    counts = sim.run(tqc, shots=shots).result().get_counts()
    
    errors = sum(c for key, c in counts.items() if key.split()[0] == "1")
    return errors / shots
    
#T6
#Design a 3-qubit circuit (no measurements) preparing the W state
#|W\rangle = \frac{1}{\sqrt3}(|001\rangle+|010\rangle+|100\rangle)
#(up to global phase) with **at most 8 gates** (any standard gates; measurements forbidden).

def design_challenge() -> QuantumCircuit:
    qc = QuantumCircuit(3)
    #q0: (1/sqrt3)|0> + sqrt(2/3)|1>
    qc.ry(2 * math.acos(1 / math.sqrt(3)), 0)  
    #split the q0=1 branch evenly over q1
    qc.ch(0, 1)                                
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.x(0) #5  total
    return qc