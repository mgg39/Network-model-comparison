import networkx as nx

import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
from netsquid.components import ClassicalChannel
from netsquid.components import QuantumChannel
from netsquid.nodes import Node, Network
from processor import create_processor
from connections import QuantumConnection, ClassicalConnection

#type : quantum, classic
#nodes : n of desired nodes
#topology (2d) : line, star, grid, cycle
#noise model : set to none for now
def network(type,nodes,topology,node_distance): #,noise_model)
    available_types = ['quantum','classic']
    available_topologies = ['star_graph','grid_2d_graph','cycle_graph']

    #-------------------------generate networkx network-----------------------
    for ty in available_types:
        if type == 'quantum':
            connection = QuantumConnection(length=node_distance, source_frequency=2e7)
        elif type == 'classic':
            connection = ClassicalConnection(length=node_distance, source_frequency=2e7)

    for to in available_topologies:
        if topology == 'star_graph':
            network = nx.star_graph(nodes)
        elif topology == 'grid_2d_graph':
            network = nx.grid_2d_graph(nodes)
        elif topology == 'cycle_graph':
            network = nx.cycle_graph(nodes)


    #-------------------------generate netsquid network-----------------------

    #append nodes
    nodes = []
    for i in range(nodes):
        node = Node(f"node_{i}", qmemory= create_processor(depolar_rate = 0, dephase_rate = 0)) #ideal case for now
        node.number = i
        nodes.append(node)
    
    network.add_nodes(nodes)

    #set up connections
    for i in range(nodes):
        j = i + 1
        while j < nodes:
            network.add_connection(nodes[i],
                                   nodes[j],
                                   label=f'conn_{i}{j}',
                                   connection=connection,
                                   port_name_node1=f'cla_%s' % j,
                                   port_name_node2=f'cla_%s' % i)
