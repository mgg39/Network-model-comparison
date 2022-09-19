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
from netsquid.util.datacollector import DataCollector

#import network generator
from protocols import Initiatesystem,Sendmessage, Readmessage
from netsquid.examples.entanglenodes import EntangleNodes
from processor import processor
from network_generator import network_generator

import time
start = time.time()
print("I am running")
end = time.time()
print(end - start)


np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)

#setting variables
nodes = 10
topology = 'star_graph'
distance = 1

def networkexperiment(nodes,t_topology,n_distance):

    print("network experiment main initiate")

    network = network_generator(nodes)

    print("set networks initiate")
    #------------------------- run network  -----------------------

    #Append protocols to nodes
    protocols = []


    for node in range(0,nodes):
        #initiating communications protocols

        if node < nodes :
            print("sending message")
            protocols.append(Sendmessage(network.nodes[node]))
            print("message sent")
        else:
            print("read message")
            protocols.append(Readmessage(network.nodes[node]))

    protocols.append(Initiatesystem(network.nodes[node]))

    #------------------------- collect the data -----------------------
    #print("collect data initiate")
    qubits_received_stats = {}
    qubit_paths = {}
    current_qubit = 0

    def collect_stats(evexpr):
        nonlocal current_qubit

        print("Collecting Signals")

        trigger = evexpr.triggered_events[-1].source
        print("Triggers: ",trigger)

        data = trigger.get_signal_result(Signals.SUCCESS)
        print("data: ",data)

        if data[1] == 2:
            print("current qubit set 2:",current_qubit)
            current_qubit += 1
        

        elif data[1] == 1:
            print("current qubit set 1:",current_qubit)
            if current_qubit not in qubit_paths: 
                qubit_paths[current_qubit] = [data[0]]                
            else:
                qubit_paths[current_qubit].append(data[0])
        
        elif data[1] == 0:
            print("current qubit set 0:",current_qubit)

            if data[0] in qubits_received_stats:
                qubits_received_stats[data[0]] += 1
            else:
                qubits_received_stats[data[0]] = 1

    print("Open Data Collector")

    dc = DataCollector(collect_stats)

    events = []
    for p in protocols:
        #print("protocol: ", p)
        #print("initiating protocol messages")
        # Make sure the start the protocol
        p.start()
        # Build up all the events to track
        #print("working through protocols")
        events.append(ns.pydynaa.EventExpression(source=p,
                                                 event_type=Signals.SUCCESS.value))
    #print("collecting outputs")
    #print("Events 2:",events)
    dc.collect_on(events, combine_rule='OR')

    #------------------------- run simulation -----------------------
    ns.sim_run()

    #------------------------- show data -----------------------
    #print("create data file")
    data = [qubit_paths[k] for k in sorted(qubit_paths.keys())]
    print("results: \n", data)
    with open('tpt3.txt', 'w') as f:
        f.writelines(["%s \n " % item  for item in data])



#------------------------- RUN -------------------------
if __name__ == '__main__':
    for i in range(0,1):
        networkexperiment(nodes, topology, distance)