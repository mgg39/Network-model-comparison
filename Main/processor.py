import netsquid as ns
import netsquid.components.instructions as instr 
import netsquid.qubits.ketstates as ks
from netsquid.components import ClassicalChannel 
from netsquid.components import PhysicalInstruction, QuantumProcessor, DepolarNoiseModel, DephaseNoiseModel

#from netsquid.qubits import 

def create_processor(depolar_rate, dephase_rate):
    measure_noise_model = DephaseNoiseModel(dephase_rate=dephase_rate,
                                            time_independent=True)
    physical_instructions = [ 
        PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=True),
        PhysicalInstruction(instr.INSTR_H, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_X, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_S, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=True), 
        PhysicalInstruction(instr.INSTR_MEASURE, 
                            duration=7, 
                            parallel=False, 
                            quantum_noise_model=measure_noise_model, 
                            apply_q_noise_after=False)
    ]
    memory_noise_model = DepolarNoiseModel(depolar_rate=depolar_rate) 
    
    processor = QuantumProcessor("quantum_processor",
                                 num_positions=1,
                                 memory_noise_models=[memory_noise_model],
                                 phys_instructions=physical_instructions)
    return processor 
    