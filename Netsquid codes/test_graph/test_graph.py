import netsquid as ns
from netsquid.components import QuantumChannel
from netsquid.nodes import Node, Network

from Connections import ClassicalConnection, EntanglingConnection, create_processor


def network_setup_with_ent_source(node_distance=4e-3, depolar_rate=0, dephase_rate=0):
    network = Network("Three Node Network with Ent Sources")

    nodes = []
    for i in range(NUM_NODES):
        node = Node(f"node_{i}", qmemory=create_processor(depolar_rate, dephase_rate))
        node.number = i
        nodes.append(node)

    network.add_nodes(nodes)

    for i in range(NUM_NODES):
        j = i + 1
        while j < NUM_NODES:
            c_conn = ClassicalConnection(name=f'c_conn_{i}{j}',
                                         length=node_distance)

            network.add_connection(nodes[i],
                                   nodes[j],
                                   label=f'c_conn_{i}{j}',
                                   connection=c_conn,
                                   port_name_node1=f'cla_%s' % j,
                                   port_name_node2=f'cla_%s' % i)
            source_frequency = 4e4 / node_distance
            q_conn = EntanglingConnection(name=f'ent_conn_{i}{j}',
                                          length=node_distance,
                                          source_frequency=source_frequency)

            port_1, port_2 = network.add_connection(
                nodes[i], nodes[j], connection=q_conn, label=f"quan_%s%s" % (i, j),
                port_name_node1=f"qin_ent_source_{i}{j}", port_name_node2=f"qin_ent_source_{i}{j}")

            nodes[i].ports[port_1].forward_input(nodes[i].qmemory.ports[f'qin{j}'])
            nodes[j].ports[port_2].forward_input(nodes[j].qmemory.ports[f'qin{i}'])
            j += 1

    return network


def create_step_tree(layers):
    network = Network("Step Tree Network")
    nodes = []

    root = Node(f"node_{0}", qmemory=create_processor(0, 0))
    root.number = 0
    root.layer = 0
    root.x = [0.5, 0.5]
    root.y = [[1, 0], [0, 1]]
    network.add_node(root)
    nodes.append(root)

    parents = [root]
    total_nodes = 1

    for layer in range(layers):
        layer_nodes = []
        for _ in range(layer + 2):
            n = Node(f"node_{total_nodes}", qmemory=create_processor(0, 0))
            n.number = total_nodes

            n.x = [0.5, 0.5]
            n.y = [[1, 0], [0, 1]]

            network.add_node(n)
            total_nodes += 1
            n.layer = layer
            layer_nodes.append(n)

        for i, parent in enumerate(parents):
            network.add_connection(parent,
                                   layer_nodes[i],
                                   label=f'q_conn_{parent.number}{layer_nodes[i].number}',
                                   channel_to=QuantumChannel(name=f'q_conn_{parent.number}{layer_nodes[i].number}'),
                                   port_name_node1=f'qua_0',
                                   port_name_node2=f'qua_p1')
            network.add_connection(parent,
                                   layer_nodes[i + 1],
                                   label=f'q_conn_{parent.number}{layer_nodes[i + 1].number}',
                                   channel_to=QuantumChannel(name=f'q_conn_{parent.number}{layer_nodes[i + 1].number}'),
                                   port_name_node1=f'qua_1',
                                   port_name_node2=f'qua_p2')
        parents = layer_nodes
    return network


def create_binary_tree_network(layers):
    network = Network("Tree Network")
    nodes = []
    root = Node(f"node_{0}", qmemory=create_processor(0, 0))
    root.number = 0
    network.add_node(root)
    nodes.append(root)

    total_nodes = 1

    def add_connections(parent):
        nonlocal total_nodes
        c1 = Node(f"node_{total_nodes}", qmemory=create_processor(0, 0))
        c2 = Node(f"node_{total_nodes + 1}", qmemory=create_processor(0, 0))
        c1.number = total_nodes
        c2.number = total_nodes + 1
        network.add_nodes([c1, c2])

        total_nodes += 2

        nodes.append(c1)
        nodes.append(c2)

        network.add_connection(parent,
                               c1,
                               label=f'q_conn_{parent.number}{c1.number}',
                               channel_to=QuantumChannel(name=f'q_conn_{parent.number}{c1.number}'),
                               port_name_node1=f'qua_0',
                               port_name_node2=f'qua_p')
        network.add_connection(parent,
                               c2,
                               label=f'q_conn_{parent.number}{c2.number}',
                               channel_to=QuantumChannel(name=f'q_conn_{parent.number}{c2.number}'),
                               port_name_node1=f'qua_1',
                               port_name_node2=f'qua_p')

    parents = [root]
    for i in range(layers):
        for p in parents:
            add_connections(p)
        parents = nodes[2 ** (i + 1) - 1: 2 ** (i + 2) - 1]

    return network