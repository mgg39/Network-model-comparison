import netsquid as ns
from netsquid.qubits.qformalism import QFormalism

from protocols import setup_protocol
from topologies import create_example_network


def run_simulation():
    """Run the example simulation.

    """
    ns.sim_reset()
    ns.set_random_state(42)  # Set the seed so we get the same outcome
    ns.set_qstate_formalism(QFormalism.DM)
    network = create_example_network()
    protocol = setup_protocol(network)
    protocol.start()
    ns.sim_run()

run_simulation()