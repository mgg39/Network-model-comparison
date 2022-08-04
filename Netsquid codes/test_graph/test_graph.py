def create_example_network(num_qubits=3):
    """Create the example network.

    Alice and Bob need a QuantumProcessor to store the qubits they produce.
    Their qubits are send through a heralded connection,
    which needs to be connected to Alice and Bob.
    It is assumed qubits are send to the connection,
    and it returns classical messages.
    In this example we won't use noise on the quantum memories,
    so instead of defining PhysicalInstructions we
    fallback to nonphysical ones.
    In order to synchronize their attempts a classical connection is added.

    Parameters
    ----------
    num_qubits : int
        The number of entangled qubit pairs we expect this network to make. Default 3.

    Returns
    -------
    :class:`~netsquid.nodes.network.Network`
        The example network for a simple link.

    """
    network = Network('SimpleLinkNetwork')
    nodes = network.add_nodes(['Alice', 'Bob'])
    distance = 2  # in km
    for node in nodes:
        node.add_subcomponent(QuantumProcessor(f'qmem_{node.name}',
                                               num_positions=num_qubits + 1,
                                               fallback_to_nonphysical=True))
    conn = HeraldedConnection("HeraldedConnection", length_to_a=distance / 2,
                              length_to_b=distance / 2, time_window=20)
    network.add_connection(nodes[0], nodes[1], connection=conn, label='quantum')
    network.add_connection(nodes[0], nodes[1], delay=distance / 200000 * 1e9, label='classical')
    return network