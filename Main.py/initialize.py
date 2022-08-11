import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.protocols import Signals

#standart generating qubits protocol to be run at a node level
class Generate_message(NodeProtocol):
    def __init__(self, node, num_qubits=100):
        super().__init__(node)
        self.num_qubits = num_qubits

    def run(self):
        for _ in range(self.num_qubits):
            # Create a qubit and put it in the memory to be forwarded
            q = ns.qubits.create_qubits(1) #modif n qubits created at once
            #Un-comment line bellow for 2D graph
            self.send_signal(Signals.SUCCESS, (self.node.number, 2)) #send signal when qubit is generated to start next subprotocol #3D data
            self.node.qmemory.put(q, 0, replace=True) #input generated qubit into memory
            yield self.await_timer(100) #timer - can be modif