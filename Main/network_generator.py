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
def network(type,n_nodes,topology,node_distance): 
    available_types = ['quantum','classic']
    available_topologies = ['star_graph','grid_2d_graph','cycle_graph','line_graph']

    #-------------------------set inputs-----------------------
    for ty in available_types:
        if type == 'quantum':
            for to in available_topologies:
                if topology == 'star_graph':
                    starq = StarTopology_q()
                    network = starq.set_network()
                elif topology == 'grid_2d_graph':
                    gridq = GridTopology_q()
                    network = gridq.set_network()
                elif topology == 'cycle_graph':
                    cycleq = CycleTopology_q()
                    network = cycleq.set_network()
                elif topology == 'line_graph':
                    lineq = LineTopology_q()
                    network = lineq.set_network()
        elif type == 'classic':
            for to in available_topologies:
                if topology == 'star_graph':
                    starc = StarTopology_c()
                    network = starc.set_network()
                elif topology == 'grid_2d_graph':
                    gridc = GridTopology_c()
                    network = gridc.set_network()
                elif topology == 'cycle_graph':
                    cyclec = CycleTopology_c()
                    network = cyclec.set_network()
                elif topology == 'line_graph':
                    linec = LineTopology_c()
                    network = linec.set_network()

        
    #-------------------------generate netsquid network-----------------------

    nodes = []
    for i in range(n_nodes):
        node = Node(f"node_{i}", qmemory= processor(depolar_rate = 0, dephase_rate = 0)) #ideal case for now
        node.number = i
        nodes.append(node)
    
    network.add_nodes(nodes)
    

    for i in range(n_nodes):
        j = i + 1
        while j < n_nodes:
            if type == 'quantum':
                source_frequency = 4e4 #arbitrartly set right now
                #setting type of connection
                q_conn = QuantumConnection(name=f'ent_conn_{i}{j}',
                                        length=node_distance,
                                        source_frequency=source_frequency)
                #adding connection to the network
                network.add_connection(nodes[i],
                                        nodes[j],
                                        label=f'conn_{i}{j}',
                                        connection=q_conn,
                                        port_name_node1=f'cla_%s' % j,
                                        port_name_node2=f'cla_%s' % i)
            else:
                c_conn = ClassicalConnection(name=f'c_conn_{i}{j}',
                                             length=node_distance)
                network.add_connection(nodes[i],
                        nodes[j],
                        label=f'conn_{i}{j}',
                        connection=c_conn,
                        port_name_node1=f'cla_%s' % j,
                        port_name_node2=f'cla_%s' % i)

    #-------------------------return network-----------------------
    return network
