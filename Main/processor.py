import netsquid as ns
import netsquid.components.instructions as instr 
import netsquid.qubits.ketstates as ks
from netsquid.components import ClassicalChannel 
from netsquid.components import PhysicalInstruction, QuantumProcessor, DepolarNoiseModel, DephaseNoiseModel

#from netsquid.qubits import 

def processor(depolar_rate, dephase_rate):
    """Factory to create a quantum processor for each end node.

    Has two memory positions and the physical instructions necessary
    for teleportation.

    Parameters
    ----------
    depolar_rate : float
        Depolarization rate of qubits in memory.
    dephase_rate : float
        Dephasing rate of physical measurement instruction.

    Returns
    -------
    :class:`~netsquid.components.qprocessor.QuantumProcessor`
        A quantum processor to specification.

    """
    # We'll give both Alice and Bob the same kind of processor
    measure_noise_model = DephaseNoiseModel(dephase_rate=dephase_rate,
                                            time_independent=True)
    physical_instructions = [
        PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=True),
        PhysicalInstruction(instr.INSTR_H, duration=1, parallel=True, topology=[0, 1]),
        PhysicalInstruction(instr.INSTR_X, duration=1, parallel=True, topology=[0]),
        PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=True, topology=[0]),
        PhysicalInstruction(instr.INSTR_S, duration=1, parallel=True, topology=[0]),
        PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=True, topology=[(0, 1)]),
        PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=[0],
                            quantum_noise_model=measure_noise_model, apply_q_noise_after=False),
        PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=[1])
    ]
    memory_noise_model = DepolarNoiseModel(depolar_rate=depolar_rate)
    processor = QuantumProcessor("quantum_processor", num_positions=2,
                                 memory_noise_models=[memory_noise_model] * 2,
                                 phys_instructions=physical_instructions)
    return processor