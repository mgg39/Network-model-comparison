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
#import data collection system
from datacollector import setup_datacollector

def run_experiment(): #(num_qubits):

    ## Initialize network ------------------------------------------
    network = Two_node_network(3,1,1)
    protocols = []

    ## Protocols ------------------------------------------
    for node in network.nodes:
        protocols.append(Forward_message(network.nodes[node]))
    
    #protocols.append(Generate_message(network.nodes['node_0'], num_qubits))

    ## Data collector ------------------------------------------
    data = setup_datacollector(network,protocols)
    print(data)

    ## Simulation ------------------------------------------
    
    # Start the simulation
    ns.sim_run()

#Run
if __name__ == '__main__':
    run_experiment() #100)
        
print("I am running")