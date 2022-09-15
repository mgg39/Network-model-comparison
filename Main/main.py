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
from protocols import Initiatesystem,Sendmessage,Sendentangledmessage, Readmessage
from processor import processor

import time
start = time.time()
print("I am still running")
end = time.time()
print(end - start)


np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)

#setting variables
nodes = 10
topology = 'star_graph'
distance = 1

def networkexperiment(nodes,t_topology,n_distance):

    network1 = network('quantum',nodes,t_topology,n_distance) #,noise_model)
    network2 = network('classic',nodes,t_topology,n_distance) #noise_model)

    #------------------------- run the network -----------------------
    def run_comparison_experiment(network):

        #Append protocols to nodes
        protocols = []
        for node in network.nodes:
            #initiating communications protocols
            protocols.append(Initiatesystem(network.nodes[node]))
            
            if network.type == 'quantum': #with entanglement
                protocols.append(Sendentangledmessage(network.nodes[node]))
            else: #classical vs
                protocols.append(Sendmessage(network.nodes[node]))
            
            #read message
            protocols.append(Readmessage(network.nodes[node]))

        #------------------------- collect the data -----------------------
        qubits_received_stats = {}
        qubit_paths = {}
        current_qubit = 0

        def collect_stats(evexpr):
            trigger = evexpr.triggered_events[-1].source

            data = trigger.get_signal_result(Signals.SUCCESS)
            
            if data[1] == 2:
                current_qubit += 1
            
            elif data[1] == 1:
                if current_qubit not in qubit_paths: 
                    qubit_paths[current_qubit] = [data[0]]                
                else:
                    qubit_paths[current_qubit].append(data[0])

            elif data[1] == 0:
                if data[0] in qubits_received_stats:
                    qubits_received_stats[data[0]] += 1
                else:
                    qubits_received_stats[data[0]] = 1


        dc = DataCollector(collect_stats)
        events = []
        for p in protocols:
            # Make sure the start the protocol
            p.start()
            # Build up all the events to track
            events.append(ns.pydynaa.EventExpression(source=p,
                                                        event_type=Signals.SUCCESS.value))

        dc.collect_on(events, combine_rule='OR')


        #------------------------- show data -----------------------
        data = [qubit_paths[k] for k in sorted(qubit_paths.keys())]
        with open('tpt3.txt', 'w') as f:
            f.writelines(["%s \n " % item  for item in data])


#------------------------- RUN -------------------------
if __name__ == '__main__':
    for i in range(1):
        networkexperiment(nodes, topology, distance)