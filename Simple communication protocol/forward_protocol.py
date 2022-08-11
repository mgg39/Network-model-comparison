from netsquid.protocols import Protocol
from netsquid.components import QuantumChannel
from netsquid.nodes import Node, DirectConnection
from netsquid.qubits import qubitapi as qapi

class Forward_message(NodeProtocol):

    def run(self):
        #Create 1 qubit
        qubit, = qapi.create_qubits(1)
        #Output time stamps
        print(f"Sending qubit at t={ns.sim_time()}")
        #Send qubit to available connected node
        port = self.node.ports["port_to_channel"]
        port.tx_output(qubit) 