#Netsquid imports
import netsquid as ns
#from netsquid.protocols import Signals
from netsquid.util import DataCollector
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.nodes import Node, Network 
from netsquid.protocols import NodeProtocol
import pydynaa

class Measure_Qubit(NodeProtocol):
    def run(self):
        def measure(message):
            self.send_signal(Signals.SUCCESS, (self.node.number, 0))
        if 'qua_p' in self.node.ports:
            self.node.ports['qua_p'].bind_input_handler(measure)
        if 'qua_p1' in self.node.ports:
            self.node.ports['qua_p1'].bind_input_handler(measure)
        if 'qua_p2' in self.node.ports:
            self.node.ports['qua_p2'].bind_input_handler(measure)

        while True:
            if 'qua_p' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p'])
            elif 'qua_p1' in self.node.ports and 'qua_p2' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p1']) | self.await_port_input(
                    self.node.ports['qua_p2'])
            elif 'qua_p1' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p1'])
            else:
                yield self.await_port_input(self.node.ports['qua_p2'])