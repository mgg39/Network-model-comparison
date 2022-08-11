#netsquid imports
import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
import netsquid.qubits.ketstates as ks #qubit state format - can be modif
from netsquid.components import ClassicalChannel #input standart classical channel class 
from netsquid.components import QuantumChannel, SourceStatus, QSource, PhysicalInstruction, \
    DepolarNoiseModel, QuantumProcessor, DephaseNoiseModel, FixedDelayModel
from netsquid.components.models import FibreDelayModel #chosen connection model for classical connections - can be modif
from netsquid.nodes.connections import Connection
from netsquid.qubits import StateSampler
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.nodes import Node, Network 

#import from connections
from connections import EntanglingConnection #Quantum channel
from connections import ClassicalConnection #Classical channel


def Two_node_network(num_qubits=3):

    network = Network('SimpleLinkNetwork')
    nodes = network.add_nodes(['Alice', 'Bob'])
    distance = 2  # in km
    for node in nodes:
        node.add_subcomponent(QuantumProcessor(f'qmem_{node.name}',
                                               num_positions=num_qubits + 1,
                                               fallback_to_nonphysical=True))
    conn = EntanglingConnection("EntanglingConnection", length_to_a=distance / 2,
                              length_to_b=distance / 2, time_window=20)
    network.add_connection(nodes[0], nodes[1], connection=conn, label='quantum')
    network.add_connection(nodes[0], nodes[1], delay=distance / 200000 * 1e9, label='classical')
    return network
