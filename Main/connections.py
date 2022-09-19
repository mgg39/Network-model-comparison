import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
import netsquid.qubits.ketstates as ks #qubit state format - can be modif
from netsquid.components import ClassicalChannel #input standart classical channel class 
from netsquid.components import QuantumChannel, SourceStatus, QSource, \
    DepolarNoiseModel, DephaseNoiseModel, FixedDelayModel
from netsquid.components.models import FibreDelayModel #chosen connection model for classical connections - can be modif
from netsquid.nodes.connections import Connection
from netsquid.qubits import StateSampler

from detector import BSMDetector

class HeraldedConnection(Connection):
    """A connection that takes in two qubits, and returns a message
    how they were measured at a detector.

    Either no clicks, a single click or double click, or an error
    when the qubits didn't arrive within the time window.

    Parameters
    ----------
    name : str
        The name of this connection
    length_to_a : float
        The length in km between the detector and side A. We assume a speed of 200000 km/s
    length_to_b : float
        The length in km between the detector and side B. We assume a speed of 200000 km/s
    time_window : float, optional
        The interval where qubits are still able to be measured correctly.
        Must be positive. Default is 0.

    """

    def __init__(self, name, length_to_a, length_to_b, time_window=0):
        super().__init__(name)
        delay_a = length_to_a / 200000 * 1e9
        delay_b = length_to_b / 200000 * 1e9
        channel_a = ClassicalChannel("ChannelA", delay=delay_a)
        channel_b = ClassicalChannel("ChannelB", delay=delay_b)
        qchannel_a = QuantumChannel("QChannelA", delay=delay_a)
        qchannel_b = QuantumChannel("QChannelB", delay=delay_b)
        # Add all channels as subcomponents
        self.add_subcomponent(channel_a)
        self.add_subcomponent(channel_b)
        self.add_subcomponent(qchannel_a)
        self.add_subcomponent(qchannel_b)
        # Add midpoint detector
        detector = BSMDetector("Midpoint", system_delay=time_window)
        self.add_subcomponent(detector)
        # Connect the ports
        self.ports['A'].forward_input(qchannel_a.ports['send'])
        self.ports['B'].forward_input(qchannel_b.ports['send'])
        qchannel_a.ports['recv'].connect(detector.ports['qin0'])
        qchannel_b.ports['recv'].connect(detector.ports['qin1'])
        channel_a.ports['send'].connect(detector.ports['cout0'])
        channel_b.ports['send'].connect(detector.ports['cout1'])
        channel_a.ports['recv'].forward_output(self.ports['A'])
        channel_b.ports['recv'].forward_output(self.ports['B'])