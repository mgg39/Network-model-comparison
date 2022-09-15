import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.protocols import Signals

class GenerateQubits(NodeProtocol):
    def __init__(self, node, num_qubits=100):
        super().__init__(node)
        self.num_qubits = num_qubits

    def run(self):
        for _ in range(self.num_qubits):
            q = ns.qubits.create_qubits(1) 
            self.send_signal(Signals.SUCCESS, (self.node.number, 2)) 
            self.node.qmemory.put(q, 0, replace=True) 
            yield self.await_timer(100) 



            