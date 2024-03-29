#netsquid imports
import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
from netsquid.components.instructions import InstructionError,INSTR_INIT, INSTR_SWAP, INSTR_UNITARY, INSTR_X, INSTR_Y, INSTR_S, INSTR_T, INSTR_Z, INSTR_H, INSTR_I, INSTR_MEASURE_BELL 
import netsquid.qubits.ketstates as ks #qubit state format - can be modif
from netsquid.components import QuantumChannel, SourceStatus, QSource, PhysicalInstruction, \
    DepolarNoiseModel, QuantumProcessor, DephaseNoiseModel, FixedDelayModel
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *


def create_qprocessor(name):
    """Factory to create a quantum processor for each node in the repeater chain network.

    Has two memory positions and the physical instructions necessary for teleportation.

    Parameters
    ----------
    name : str
        Name of the quantum processor.

    Returns
    -------
    :class:`~netsquid.components.qprocessor.QuantumProcessor`
        A quantum processor to specification.

    """
    noise_rate = 200
    gate_duration = 1
    gate_noise_model = DephaseNoiseModel(noise_rate)
    mem_noise_model = DepolarNoiseModel(noise_rate)
    physical_instructions = [
        PhysicalInstruction(INSTR_X, duration=gate_duration,
                            quantum_noise_model=gate_noise_model),
        PhysicalInstruction(INSTR_Z, duration=gate_duration,
                            quantum_noise_model=gate_noise_model),
        PhysicalInstruction(INSTR_MEASURE_BELL, duration=gate_duration),
    ]
    qproc = QuantumProcessor(name, num_positions=2, fallback_to_nonphysical=False,
                             mem_noise_models=[mem_noise_model] * 2,
                             phys_instructions=physical_instructions)
    return qproc