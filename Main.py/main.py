#Netsquid imports
import netsquid as ns
#from netsquid.protocols import Signals
from netsquid.util import DataCollector
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.nodes import Node, Network 
from netsquid.protocols import NodeProtocol


#import topology 
from network import Two_node_network
#import forwarding protocol 
from protocol import Forward_message
#import generating qubits initial protocol
from initialize import Generate_message


#Common warning
#np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)

def Run_experiment(num_qubits):

    ## Initialize network ------------------------------------------
    network = Two_node_network(3)
    protocols = []
    measure_protocols = []
    measure_node_nums = []

    ## Protocols ------------------------------------------
    for node in network.nodes:
        protocols.append(Forward_message(network.nodes[node]))
    
    protocols.append(Generate_message(network.nodes['node_0'], num_qubits))

    ## Simulation ------------------------------------------
    
    # Start the simulation
    ns.sim_run()

#Run
if __name__ == '__main__':
    # run the experiment x times
    for i in range(1):
        #n layers considers 1st node to be in layer 0
        Run_experiment(num_qubits=100)

##----------------------------------------------------------------

def run_simulation(num_nodes=4, node_distance=20, num_iters=100):
    """Run the simulation experiment and return the collected data.

    Parameters
    ----------
    num_nodes : int, optional
        Number nodes in the repeater chain network. At least 3. Default 4.
    node_distance : float, optional
        Distance between nodes, larger than 0. Default 20 [km].
    num_iters : int, optional
        Number of simulation runs. Default 100.

    Returns
    -------
    :class:`pandas.DataFrame`
        Dataframe with recorded fidelity data.

    """
    ns.sim_reset()
    est_runtime = (0.5 + num_nodes - 1) * node_distance * 5e3
    network = setup_network(num_nodes, node_distance=node_distance,
                            source_frequency=1e9 / est_runtime)
    protocol = setup_repeater_protocol(network)
    dc = setup_datacollector(network, protocol)
    protocol.start()
    ns.sim_run(est_runtime * num_iters)
    return dc.dataframe