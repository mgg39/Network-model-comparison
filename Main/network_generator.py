import netsquid as ns
from netsquid.components import QuantumChannel
from netsquid.nodes import Node, Network

from topologies import LineTopology_q
from processor import processor

def network_generator(node_n):
    network = Network("Line Network q")
    nodes = []

    for i in range(node_n):
        node = Node(f"node_{i}", qmemory=processor(0, 0))
        node.number = 1
        nodes.append(node)

    return network