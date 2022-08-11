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
#import protocol 
from protocol import Forward_message

#Common warning
#np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)

def Run_experiment(num_qubits):

    #Initialize network
    network = Two_node_network()
    protocols = []
    measure_protocols = []
    measure_node_nums = []

    