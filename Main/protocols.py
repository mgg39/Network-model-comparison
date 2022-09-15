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


class Initiatesystem(NodeProtocol):

    def __init__(self, node, num_qubits=100):
        super().__init__(node)
        self.num_qubits = num_qubits

    def run(self):
        for _ in range(self.num_qubits):
            q = ns.qubits.create_qubits(1) 
            self.send_signal(Signals.SUCCESS, (self.node.number, 2)) 
            self.node.qmemory.put(q, 0, replace=True) 
            yield self.await_timer(100) 


class Sendmessage(NodeProtocol):

    def run(self):
        def forward(message):

            self.send_signal(Signals.SUCCESS, (self.node.number, 1))
            qubit = message.items[0]
            operate(qubit, ops.H)
            
            if 'rx_port_name' in message.meta:
                port = 1 if message.meta['rx_port_name'] == 'qua_p1' else 0
            else:
                port = 0
            
            self.node.y[port] = qubit.qstate.qrepr.ket
            self.node.x[port] = lr * self.node.x[port] + (1 - lr)
            self.node.x[1 - port] = lr * self.node.x[1 - port]
            

            p = np.random.random()            
            if np.random.random() < p:
                ns.qubits.qubitapi.assign_qstate([qubit], np.array([w[0], w[2]]) / sqrt(p))
                final_port = 0
            else:
                ns.qubits.qubitapi.assign_qstate([qubit], np.array([w[1], w[3]]) / sqrt(1 - p))
                final_port = 1

            self.node.ports[f'qua_{final_port}'].tx_output(message)
        
        self.node.qmemory.ports['qout'].bind_output_handler(forward)
        if 'qua_p' in self.node.ports:
            self.node.ports['qua_p'].bind_input_handler(forward)
        if 'qua_p1' in self.node.ports:
            self.node.ports['qua_p1'].bind_input_handler(forward, tag_meta=True)
        if 'qua_p2' in self.node.ports:
            self.node.ports['qua_p2'].bind_input_handler(forward, tag_meta=True)

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


class Sendentangledmessage(NodeProtocol):

    def run(self):
        while True:
            if self.start_expression is not None:
                yield self.start_expression
            elif self._is_source and self.entangled_pairs >= self._num_pairs:
                # If no start expression specified then limit generation to one round
                break
            for mem_pos in self._mem_positions[::-1]:
                # Iterate in reverse so that input_mem_pos is handled last
                if self._is_source:
                    self.node.subcomponents[self._qsource_name].trigger()
                yield self.await_port_input(self._qmem_input_port)
                if mem_pos != self._input_mem_pos:
                    self.node.qmemory.execute_instruction(
                        #this SWAP is present within our protocol through the Beam Splitter's
                        #density matrix performed SWAP
                        INSTR_SWAP, [self._input_mem_pos, mem_pos])
                    if self.node.qmemory.busy:
                        yield self.await_program(self.node.qmemory)
                self.entangled_pairs += 1
                self.send_signal(Signals.SUCCESS, mem_pos)


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
            else:
                yield self.await_port_input(self.node.ports['qua_p2'])