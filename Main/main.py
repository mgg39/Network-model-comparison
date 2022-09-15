# import sys
# import tk
import matplotlib.pyplot as plt #useful for data outputs
import numpy as np #useful for data outputs

#import netsquid & basic requirements
import netsquid as ns
from netsquid.protocols import Signals
from netsquid.util import DataCollector
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.nodes import Node, Network 
from netsquid.protocols import NodeProtocol

#import network generator
from network_generator import network

np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)

 #-------------------------generate netsquid network-----------------------
#setting variables
n_nodes = 10
t_topology = 'line'
n_distance = 1

network1 = network('quantum',n_nodes,t_topology,n_distance) #,noise_model)
network2 = network('classic',n_nodes,t_topology,n_distance) #noise_model)

 #-------------------------run the network-----------------------
def run_comparison_experiment(network):

    #Append protocols to nodes
    for node in network.nodes:
        #initiating communications protocols

        #simple layer protocols
        if network.type == 'quantum': #with entanglement
            
        else: #classical vs
            
