#Netsquid imports
import netsquid as ns
from netsquid.protocols import Signals
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

    #Initialize network
    network = Two_node_network()
    protocols = []
    measure_protocols = []
    measure_node_nums = []

    for node in network.nodes:
        protocols.append(Forward_message(network.nodes[node]))
    
    protocols.append(Generate_message(network.nodes['node_0'], num_qubits))