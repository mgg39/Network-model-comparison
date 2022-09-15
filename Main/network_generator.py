import networkx as nx

import netsquid as ns
import netsquid.components.instructions as instr #instructions that can be followed by the processor
from netsquid.nodes import Node, Network
from processor import processor
from connections import QuantumConnection, ClassicalConnection
from topologies import StarTopology_q,GridTopology_q,CycleTopology_q,LineTopology_q,StarTopology_c,GridTopology_c,CycleTopology_c,LineTopology_c

#type : quantum, classic
#nodes : n of desired nodes
#topology (2d) : line, star, grid, cycle
#noise model : set to none for now
def network(type,n_nodes,topology,node_distance): #,noise_model)
    available_types = ['quantum','classic']
    available_topologies = ['star_graph','grid_2d_graph','cycle_graph','line_graph']
    protocols = []

    #-------------------------set inputs-----------------------
    for ty in available_types:
        if type == 'quantum':
            for to in available_topologies:
                if topology == 'star_graph':
                    network = protocols.append(StarTopology_q(network.nodes[node]))
                elif topology == 'grid_2d_graph':
                    network = protocols.append(GridTopology_q(network.nodes[node]))
                elif topology == 'cycle_graph':
                    network = protocols.append(CycleTopology_q(network.nodes[node]))
                elif topology == 'line_graph':
                    network = protocols.append(LineTopology_q(network.nodes[node]))
        elif type == 'classic':
            for to in available_topologies:
                if topology == 'star_graph':
                    network = protocols.append(StarTopology_c(network.nodes[node]))
                elif topology == 'grid_2d_graph':
                    network = protocols.append(GridTopology_c(network.nodes[node]))
                elif topology == 'cycle_graph':
                    network = protocols.append(CycleTopology_c(network.nodes[node]))
                elif topology == 'line_graph':
                    network = protocols.append(LineTopology_c(network.nodes[node]))

        
    #-------------------------generate netsquid network-----------------------

    #append nodes
    nodes = []
    for i in range(n_nodes):
        node = Node(f"node_{i}", qmemory= processor(depolar_rate = 0, dephase_rate = 0)) #ideal case for now
        node.number = i
        nodes.append(node)
    
    network.add_nodes(nodes)

    #set up connections
    for i in range(n_nodes):
        j = i + 1
        while j < nodes:
            network.add_connection(nodes[i],
                                   nodes[j],
                                   label=f'conn_{i}{j}',
                                   connection=connection,
                                   port_name_node1=f'cla_%s' % j,
                                   port_name_node2=f'cla_%s' % i)

    #-------------------------return network-----------------------
    return network
