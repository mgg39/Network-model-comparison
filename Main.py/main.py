
#Netsquid imports
import netsquid as ns
import pydynaa as pd
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
from datacollector import Measure_Qubit

def run_experiment(num_qubits):

    ## Initialize network ------------------------------------------
    network = Two_node_network(4,1,1)
    protocols = []
    measure_protocols = []
    measure_node_nums = []

    ## Protocols ------------------------------------------
    for node in network.nodes:
        f = Forward_message(network.nodes[node])
        measure_node_nums.append(f)

        m = Measure_Qubit(network.nodes[node])
        protocols.append(m)
        measure_protocols.append(m)    
        protocols.append(Generate_message(network.nodes[node],num_qubits))#'node_0'], num_qubits))
    

    ## Data collector ------------------------------------------
    
    # Initialize something to store the simulation data
    qubits_received_stats = {}
    current_qubit = 0

    # The function for how to handle the event triggers
    def collect_stats(evexpr):
        nonlocal current_qubit
        # Get the last event triggered
        trigger = evexpr.triggered_events[-1].source

        # Extract the data from that event
        data = trigger.get_signal_result(Signals.SUCCESS)
        
        if data[1] == 2:
            #print("test2")
            current_qubit += 1
        

        # The data collector received the node number and the output
        # of the measurement from the protocol. Simply record that
        # the event happened.
        elif data[1] == 0:
            if data[0] in qubits_received_stats:
                qubits_received_stats[data[0]] += 1
            else:
                qubits_received_stats[data[0]] = 1


    # Set the collector function
    dc = DataCollector(collect_stats)
    events = []
    for p in protocols:
        # Make sure the start the protocol
        p.start()
        # Build up all the events to track
        events.append(ns.pydynaa.EventExpression(source=p,
                                                 event_type=Signals.SUCCESS.value))

    # We want to collect data for all protocols running concurrently, use "OR"
    dc.collect_on(events, combine_rule='OR')
    
    ## Simulation ------------------------------------------
    # Start the simulation
    ns.sim_run()

#Run
if __name__ == '__main__':
    run_experiment(1)
        
print("I have ran")