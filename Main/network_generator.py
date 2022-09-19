from re import I
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

    #print("chose and set up topology")
        
    #-------------------------generate netsquid network-----------------------

    nodes = []
    for i in range(n_nodes):
        node = Node(f"node_{i}", qmemory= processor(depolar_rate = 0, dephase_rate = 0)) #ideal case for now
        node.number = i
        nodes.append(node)
    
    network.add_nodes(nodes)

    """
    #Testing
    print(network)
    print(network.nodes)
    print(network.connections)
    """

    """  
    print("set up network")
    print("n_nodes:",n_nodes)
    for i in range(0,n_nodes):
        j = i + 1
        print("j:",j)
        print("i:",i)

        while j <= n_nodes:
    
            #print("started filling networks")
            if type == 'quantum':
                print("creating a quantum network")
                source_frequency = 4e4 #arbitrartly set right now
                #setting type of connection
                q_conn = QuantumConnection(name=f'ent_conn_{i}{j}',
                                        length=node_distance,
                                        source_frequency=source_frequency)
                #adding connection to the network
                network.add_connection(nodes[i],
                                       nodes[j],
                                       label=f'qonn_{i}{j}',
                                       connection=q_conn,
                                       port_name_node1=f'qla_%s' % j,
                                       port_name_node2=f'qla_%s' % i)
                
                port_1, port_2 = network.add_connection(nodes[i], nodes[j], connection=q_conn, label=f"quan_%s%s" % (i, j),
                                                        port_name_node1=f"qin_ent_source_{i}{j}", port_name_node2=f"qin_ent_source_{i}{j}")
            
                nodes[i].ports[port_1].forward_input(nodes[i].qmemory.ports[f'qin{j}'])
                nodes[j].ports[port_2].forward_input(nodes[j].qmemory.ports[f'qin{i}'])
                
                j += 1

            else:
                print("doing classical network")
                c_conn = ClassicalConnection(name=f'c_conn_{i}{j}',
                                                length=node_distance)
                network.add_connection(nodes[i],
                        nodes[j],
                        label=f'conn_{i}{j}',
                        connection=c_conn,
                        port_name_node1=f'cla_%s' % j,
                        port_name_node2=f'cla_%s' % i)
                
                port_1, port_2 = network.add_connection(
                                nodes[i], nodes[j], connection=q_conn, label=f"cuan_%s%s" % (i, j),
                                port_name_node1=f"cin_ent_source_{i}{j}", port_name_node2=f"cin_ent_source_{i}{j}")
                
                nodes[i].ports[port_1].forward_input(nodes[i].qmemory.ports[f'cin{j}'])
                nodes[j].ports[port_2].forward_input(nodes[j].qmemory.ports[f'cin{i}'])
                
                j += 1
        """                                    

        #network.type = type
    
    #-------------------------return network-----------------------
    
    return network
