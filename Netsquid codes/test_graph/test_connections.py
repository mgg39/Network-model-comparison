import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
import netsquid.qubits.ketstates as ks #qubit state format - can be modif
from netsquid.components import ClassicalChannel #input standart classical channel class 
from netsquid.components import QuantumChannel, SourceStatus, QSource, PhysicalInstruction, \
    DepolarNoiseModel, QuantumProcessor, DephaseNoiseModel, FixedDelayModel
from netsquid.components.models import FibreDelayModel #chosen connection model for classical connections - can be modif
from netsquid.nodes.connections import Connection
from netsquid.qubits import StateSampler

#ClassicalConnection ------------------------------------------------------------------------------------------
#Classical connection class: set to transmit classical bits without any quantum effect
class ClassicalConnection(Connection):

    def __init__(self, length, name="ClassicalConnection"):
        super().__init__(name=name)
        self.add_subcomponent(ClassicalChannel("Channel_A2B",
                                               length=length, #you can modify the length associated with the connection
                                               models={"delay_model": FibreDelayModel()}), #as well as the model
                              #naming input and output ports
                              forward_input=[("A", "send")],
                              forward_output=[("B", "recv")]) 

#EntanglingConnection ------------------------------------------------------------------------------------------
#Quantum connection class: set to transmit qubits with quantum effects -> entanglement, state interactions, teleportation
class EntanglingConnection(Connection):

    def __init__(self, length, source_frequency, name="EntanglingConnection"): #you can modif length & frequency
        super().__init__(name=name)
        qsource = QSource(f"qsource_{name}",
                          StateSampler([ks.b00], [1.0]),
                          num_ports=2, #in and out port <- more ports can be added to a connection model
                          timing_model=FixedDelayModel(delay=1e9 / source_frequency), #timing model can be modif
                          status=SourceStatus.INTERNAL)
        self.add_subcomponent(qsource, #qubit source
                              name=f"qsource_{name}")
        qchannel_1 = QuantumChannel(f"qchannel_1_{name}",
                                    length=length / 2,
                                    models={"delay_model": FibreDelayModel()})
        qchannel_2 = QuantumChannel(f"qchannel_2__{name}",
                                    length=length / 2,
                                    models={"delay_model": FibreDelayModel()})

        # Add channels and forward quantum channel output to external port output:
        self.add_subcomponent(qchannel_1, forward_output=[("A", "recv")])
        self.add_subcomponent(qchannel_2, forward_output=[("B", "recv")])

        # Connect qsource output to quantum channel input:
        qsource.ports["qout0"].connect(qchannel_1.ports["send"])
        qsource.ports["qout1"].connect(qchannel_2.ports["send"])

# Processor ------------------------------------------------------------------------------------------
def create_processor(depolar_rate, dephase_rate):
    # We'll give both Alice and Bob the same kind of processor
    measure_noise_model = DephaseNoiseModel(dephase_rate=dephase_rate,
                                            time_independent=True)
    physical_instructions = [ #instructions the processor can follow (processors can be added to nodes)
        PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=True),
        PhysicalInstruction(instr.INSTR_H, duration=1, parallel=True), #Hadamard gate
        PhysicalInstruction(instr.INSTR_X, duration=1, parallel=True), #X operation
        PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=True), #Z operation
        PhysicalInstruction(instr.INSTR_S, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=True), #CNOT gate
        PhysicalInstruction(instr.INSTR_MEASURE, #Measuring incoming qubit instruction
                            duration=7, #timer - can be modif
                            parallel=False, 
                            quantum_noise_model=measure_noise_model, #noise model can be modif
                            apply_q_noise_after=False)
    ]
    memory_noise_model = DepolarNoiseModel(depolar_rate=depolar_rate) #noise model choice
    
    #memory positions associated with processor (1)
    processor = QuantumProcessor("quantum_processor",
                                 num_positions=1,
                                 memory_noise_models=[memory_noise_model],
                                 phys_instructions=physical_instructions)
    return processor #end processor
    