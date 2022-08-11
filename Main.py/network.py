#numpy
import numpy as np

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
from qprocessor import create_qprocessor #Processor


def Two_node_network(num_nodes, node_distance, source_frequency):

    """Setup repeater chain network.

    Parameters
    ----------
    num_nodes : int
        Number of nodes in the network, at least 3.
    node_distance : float
        Distance between nodes [km].
    source_frequency : float
        Frequency at which the sources create entangled qubits [Hz].

    Returns
    -------
    :class:`~netsquid.nodes.network.Network`
        Network component with all nodes and connections as subcomponents.

    """
    if num_nodes < 3:
        raise ValueError(f"Can't create repeater chain with {num_nodes} nodes.")
    network = Network("Repeater_chain_network")
    # Create nodes with quantum processors
    nodes = []
    for i in range(num_nodes):
        # Prepend leading zeros to the number
        num_zeros = int(np.log10(num_nodes)) + 1
        nodes.append(Node(f"Node_{i:0{num_zeros}d}", qmemory=create_qprocessor(f"qproc_{i}")))
    network.add_nodes(nodes)
    # Create quantum and classical connections:
    for i in range(num_nodes - 1):
        node, node_right = nodes[i], nodes[i + 1]
        # Create quantum connection
        qconn = EntanglingConnection(name=f"qconn_{i}-{i+1}", length=node_distance,
                                     source_frequency=source_frequency)
        # Add a noise model which depolarizes the qubits exponentially
        # depending on the connection length
        for channel_name in ['qchannel_C2A', 'qchannel_C2B']:
            qconn.subcomponents[channel_name].models['quantum_noise_model'] =\
                FibreDepolarizeModel()
        port_name, port_r_name = network.add_connection(
            node, node_right, connection=qconn, label="quantum")
        # Forward qconn directly to quantum memories for right and left inputs:
        node.ports[port_name].forward_input(node.qmemory.ports["qin0"])  # R input
        node_right.ports[port_r_name].forward_input(
            node_right.qmemory.ports["qin1"])  # L input
        # Create classical connection
        cconn = ClassicalConnection(name=f"cconn_{i}-{i+1}", length=node_distance)
        port_name, port_r_name = network.add_connection(
            node, node_right, connection=cconn, label="classical",
            port_name_node1="ccon_R", port_name_node2="ccon_L")
        # Forward cconn to right most node
        if "ccon_L" in node.ports:
            node.ports["ccon_L"].bind_input_handler(
                lambda message, _node=node: _node.ports["ccon_R"].tx_output(message))
    return network
