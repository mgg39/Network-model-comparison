import numpy as np
from numpy import sqrt
from numpy.random import rand

import netsquid as ns
from netsquid.nodes import Node, Network
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.qubits import operators as ops
from netsquid.protocols import NodeProtocol
from netsquid.protocols import Signals
from netsquid.components import QuantumChannel
from netsquid.nodes import Node, DirectConnection
from netsquid.qubits import qubitapi as qapi

class Initiatesystem(NodeProtocol):

    def __init__(self, node, num_qubits=100):
        super().__init__(node)
        self.num_qubits = num_qubits

    def run(self):
        for _ in range(self.num_qubits):
            q = ns.qubits.create_qubits(1) 
            self.send_signal(Signals.SUCCESS, 0) 
            self.node.qmemory.put(q, 0, replace=True) 
            yield self.await_timer(100) 


class Sendmessage(NodeProtocol):

   def run(self):

        print(f"Starting ping at t={ns.sim_time()}")
        port = self.node.ports["port_to_channel"]
        qubit, = qapi.create_qubits(1)
        port.tx_output(qubit)  # Send qubit to Pong

        while True:

            # Wait for qubit to be received back
            yield self.await_port_input(port)
            qubit = port.rx_input().items[0]
            m, prob = qapi.measure(qubit, ns.Z)
            labels_z =  ("|0>", "|1>")

            print(f"{ns.sim_time()}: Pong event! {self.node.name} measured "
                  f"{labels_z[m]} with probability {prob:.2f}")
            port.tx_output(qubit)  


class Readmessage(NodeProtocol):

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
            elif 'qua_p2' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p2'])
            else:
                yield self.await_port_input(self.node.qmemory.ports['qin'])
                self.node.qmemory.pop(0)
           