import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
import netsquid.qubits.ketstates as ks #qubit state format - can be modif
from netsquid.components import ClassicalChannel #input standart classical channel class 
from netsquid.components import QuantumChannel, SourceStatus, QSource, \
    DepolarNoiseModel, DephaseNoiseModel, FixedDelayModel
from netsquid.components.models import FibreDelayModel #chosen connection model for classical connections - can be modif
from netsquid.nodes.connections import Connection
from netsquid.qubits import StateSampler


class ClassicalConnection(Connection):

    def __init__(self, length, name="ClassicalConnection"):
        super().__init__(name=name)
        self.add_subcomponent(ClassicalChannel("Channel_A2B",
                                               length=length, 
                                               models={"delay_model": FibreDelayModel()}), 
                              forward_input=[("A", "send")],
                              forward_output=[("B", "recv")]) 


class QuantumConnection(Connection):

    def __init__(self, length, source_frequency, name="QuantumConnection"): 
        super().__init__(name=name)
        qsource = QSource(f"qsource_{name}",
                          StateSampler([ks.b00], [1.0]),
                          num_ports=2, 
                          timing_model=FixedDelayModel(delay=1e9 / source_frequency), 
                          status=SourceStatus.INTERNAL)
        self.add_subcomponent(qsource, 
                              name=f"qsource_{name}")
        qchannel_1 = QuantumChannel(f"qchannel_1_{name}",
                                    length=length / 2,
                                    models={"delay_model": FibreDelayModel()})
        qchannel_2 = QuantumChannel(f"qchannel_2__{name}",
                                    length=length / 2,
                                    models={"delay_model": FibreDelayModel()})

        self.add_subcomponent(qchannel_1, forward_output=[("A", "recv")])
        self.add_subcomponent(qchannel_2, forward_output=[("B", "recv")])

        qsource.ports["qout0"].connect(qchannel_1.ports["send"])
        qsource.ports["qout1"].connect(qchannel_2.ports["send"])
