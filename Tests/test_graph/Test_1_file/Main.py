import netsquid as ns
from numpy import sqrt
from numpy.random import rand
import matplotlib.pyplot as plt #useful for data outputs
import numpy as np #useful for data outputs
from re import I

import netsquid.components.instructions as instr #instructions that can be followed by the processor
import netsquid.qubits.ketstates as ks #qubit state format - can be modif
from netsquid.components import ClassicalChannel #input standart classical channel class 
from netsquid.components import QuantumChannel, \
    DepolarNoiseModel, DephaseNoiseModel, FixedDelayModel
from netsquid.components.models import FibreDelayModel #chosen connection model for classical connections - can be modif
from netsquid.nodes.connections import Connection
import netsquid.qubits.ketstates as ks
from netsquid.nodes import Node, Network
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.qubits import operators as ops
from netsquid.protocols import NodeProtocol
from netsquid.protocols import Signals
from netsquid.util import DataCollector
from netsquid.components.qprocessor import PhysicalInstruction, QuantumProcessor
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.qubits.state_sampler import StateSampler
from netsquid.components.qdetector import QuantumDetector
from netsquid.components.models.qerrormodels import FibreLossModel

class ClassicalConnection(Connection):

    def __init__(self, length, name="ClassicalConnection"):
        super().__init__(name=name)
        self.add_subcomponent(ClassicalChannel("Channel_A2B",
                                               length=length, 
                                               models={"delay_model": FibreDelayModel()}), 
                              forward_input=[("A", "send")],
                              forward_output=[("B", "recv")]) 


class QuantumConnection(Connection):

    def __init__(self, length, source_frequency, name="QuantumConnection"): 
        super().__init__(name=name)
        qsource = QSource(f"qsource_{name}",
                          StateSampler([ks.b00], [1.0]),
                          num_ports=2, 
                          timing_model=FixedDelayModel(delay=1e9 / source_frequency), 
                          status=SourceStatus.INTERNAL)
        self.add_subcomponent(qsource, 
                              name=f"qsource_{name}")
        qchannel_1 = QuantumChannel(f"qchannel_1_{name}",
                                    length=length / 2,
                                    models={"delay_model": FibreDelayModel()})
        qchannel_2 = QuantumChannel(f"qchannel_2__{name}",
                                    length=length / 2,
                                    models={"delay_model": FibreDelayModel()})

        self.add_subcomponent(qchannel_1, forward_output=[("A", "recv")])
        self.add_subcomponent(qchannel_2, forward_output=[("B", "recv")])

        qsource.ports["qout0"].connect(qchannel_1.ports["send"])
        qsource.ports["qout1"].connect(qchannel_2.ports["send"])

def processor(depolar_rate, dephase_rate):
    measure_noise_model = DephaseNoiseModel(dephase_rate=dephase_rate,
                                            time_independent=True)
    physical_instructions = [ 
        PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=True),
        PhysicalInstruction(instr.INSTR_H, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_X, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_S, duration=1, parallel=True), 
        PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=True), 
        PhysicalInstruction(instr.INSTR_MEASURE, 
                            duration=7, 
                            parallel=False, 
                            quantum_noise_model=measure_noise_model, 
                            apply_q_noise_after=False)
    ]
    memory_noise_model = DepolarNoiseModel(depolar_rate=depolar_rate) 
    
    processor = QuantumProcessor("quantum_processor",
                                 num_positions=1,
                                 memory_noise_models=[memory_noise_model],
                                 phys_instructions=physical_instructions)
    return processor 
    
#Standart topology class
class _Topology:
    def __init__(self,
                 name: str = 'network',
                 fibre_lengths: dict = None
                 ):
        self.name = name
        self.fibre_lengths = fibre_lengths
        self.network = None

    @staticmethod
    def create_processor(q_source_meta: dict, q_detect_meta: dict, mem_size=1000):
        # TODO: Add noise model for instructions
        # TODO: Add more instructions or allow as parameter
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False),
            PhysicalInstruction(instr.INSTR_X, duration=1, parallel=False),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False),
            PhysicalInstruction(instr.INSTR_CNOT, duration=5, parallel=False)
        ]
        # Use 2 memory positions
        # - One for outgoing quantum
        # - One for incoming quantum
        processor = QuantumProcessor(name="quantum_processor",
                                     num_positions=2,
                                     phys_instructions=physical_instructions)
        buffer = QuantumProcessor(name="quantum_buffer", num_positions=mem_size)

        qubit_source = QSource('qubit_source',
                               StateSampler([ks.s0, ks.s1], list(q_source_meta['probs'])),
                               frequency=q_source_meta['freq'],
                               num_ports=1,
                               status=SourceStatus.OFF)
        qubit_detector_z = QuantumDetector('qubit_detector_z',
                                           system_delay=q_detect_meta['sys_delay'],
                                           dead_time=q_detect_meta['dead_time'])
        qubit_detector_x = QuantumDetector('qubit_detector_x',
                                           system_delay=q_detect_meta['sys_delay'],
                                           dead_time=q_detect_meta['dead_time'],
                                           observable=ops.X)

        processor.add_subcomponent(buffer)
        processor.add_subcomponent(qubit_source)
        processor.add_subcomponent(qubit_detector_z)
        processor.add_subcomponent(qubit_detector_x)

        return processor

#--------------------------------------Grid Topology-------------------------------------------------------

#Classical version
class GridTopology_c(_Topology):
    def __init__(self, m: int, n: int = None, use_diagonal_connections: bool = False):
        super().__init__(name='grid_network')
        self.m = m
        self.n = m if n is None else n
        self.use_diagonal_connections = use_diagonal_connections
        self.nodes = []
        self.network = self.set_network()

    def set_network(self, length=1, loss=(0, 0)):
        network = Network("Grid Network")
        self.nodes = []

        def get_channels(i1, j1, i2, j2):
            c_chan_out = generate_classical_channel(name='%d%d_%d%d_chan_cla' % (i1, j1, i2, j2),
                                                    length=length)
            c_chan_in = generate_classical_channel(name='%d%d_%d%d_chan_cla' % (i2, j2, i1, j1),
                                                   length=length)
            return [c_chan_out, c_chan_in]

        for i in range(self.m):
            row = []
            for j in range(self.n):
                node = Node(f"%d%d" % (i, j),
                            qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                               {'sys_delay': 0, 'dead_time': 0}))
                row.append(node)
                network.add_node(node)
            self.nodes.append(row)
        for i in range(self.m):
            for j in range(self.n):
                links_to_add = []
                if i < self.m - 1:
                    i_to = i + 1
                    j_to = j
                    links_to_add.append((i_to, j_to))
                if j < self.n - 1:
                    i_to = i
                    j_to = j + 1
                    links_to_add.append((i_to, j_to))

                if self.use_diagonal_connections:
                    if i < self.m - 1 and j < self.n - 1:
                        i_to = i + 1
                        j_to = j + 1
                        links_to_add.append((i_to, j_to))
                    if j > 0 and i < self.m - 1:
                        i_to = i + 1
                        j_to = j - 1
                        links_to_add.append((i_to, j_to))

                for link in links_to_add:
                    channels = get_channels(i, j, link[0], link[1])

                    network.add_connection(self.nodes[i][j],
                                           self.nodes[link[0]][link[1]],
                                           label='%d%d_%d%d_cla_chan',
                                           channel_to=channels[2],
                                           channel_from=channels[3],
                                           port_name_node1=f'port_%d%d_cla' % (link[0], link[1]),
                                           port_name_node2=f'port_%d%d_cla' % (i, j)
                                           )
        return network


#Quantum version
class GridTopology_q(_Topology):
    def __init__(self, m: int, n: int = None, use_diagonal_connections: bool = False):
        super().__init__(name='grid_network')
        self.m = m
        self.n = m if n is None else n
        self.use_diagonal_connections = use_diagonal_connections
        self.nodes = []
        self.network = self.set_network()

    def set_network(self, length=1, loss=(0, 0)):
        network = Network("Grid Network")
        self.nodes = []

        def get_channels(i1, j1, i2, j2):
            q_chan_out = generate_quantum_channel(name='%d%d_%d%d_chan_quan' % (i1, j1, i2, j2),
                                                  length=length,
                                                  loss=loss)
            q_chan_in = generate_quantum_channel(name='%d%d_%d%d_chan_quan' % (i2, j2, i1, j1),
                                                 length=length,
                                                 loss=loss)

            return [q_chan_out, q_chan_in]

        for i in range(self.m):
            row = []
            for j in range(self.n):
                node = Node(f"%d%d" % (i, j),
                            qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                               {'sys_delay': 0, 'dead_time': 0}))
                row.append(node)
                network.add_node(node)
            self.nodes.append(row)
        for i in range(self.m):
            for j in range(self.n):
                links_to_add = []
                if i < self.m - 1:
                    i_to = i + 1
                    j_to = j
                    links_to_add.append((i_to, j_to))
                if j < self.n - 1:
                    i_to = i
                    j_to = j + 1
                    links_to_add.append((i_to, j_to))

                if self.use_diagonal_connections:
                    if i < self.m - 1 and j < self.n - 1:
                        i_to = i + 1
                        j_to = j + 1
                        links_to_add.append((i_to, j_to))
                    if j > 0 and i < self.m - 1:
                        i_to = i + 1
                        j_to = j - 1
                        links_to_add.append((i_to, j_to))

                for link in links_to_add:
                    channels = get_channels(i, j, link[0], link[1])
                    network.add_connection(self.nodes[i][j],
                                           self.nodes[link[0]][link[1]],
                                           label='%d%d_%d%d_quan_chan',
                                           channel_to=channels[0],
                                           channel_from=channels[1],
                                           port_name_node1=f'port_%d%d_quan' % (link[0], link[1]),
                                           port_name_node2=f'port_%d%d_quan' % (i, j)
                                           )
        return network


#--------------------------------------Star Topology-------------------------------------------------------

#Classical version
class StarTopology_c(_Topology):
    def __init__(self, num_edges: int = 5):
        super().__init__()
        self.num_edges = num_edges
        self.center = None
        self.edges = []
        self.network = self.set_network(num_edges)

    def set_network(self, length=1, loss=(0, 0)):
        network = Network("Star Network")
        self.edges = []
        center = Node('center',
                      qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                         {'sys_delay': 0, 'dead_time': 0}))
        nodes = [center]
        self.center = center
        for i in range(self.num_edges):
            node = Node(str(i),
                        qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                           {'sys_delay': 0, 'dead_time': 0}))
            nodes.append(node)
            self.edges.append(node)
        network.add_nodes(nodes)

        for i in range(self.num_edges):

            c_chan_out = generate_classical_channel(name='center->' + str(i) + '_chan_cla',
                                                    length=length)
            c_chan_in = generate_classical_channel(name='center<-' + str(i) + '_chan_cla',
                                                   length=length)
            network.add_connection(center,
                                   self.edges[i],
                                   label='center-' + str(i) + '_cla',
                                   channel_to=c_chan_out,
                                   channel_from=c_chan_in,
                                   port_name_node1='port_' + str(i) + '_cla',
                                   port_name_node2='center_cla'
                                   )
        return network


#Quantum version
class StarTopology_q(_Topology):
    def __init__(self, num_edges: int = 5):
        super().__init__()
        self.num_edges = num_edges
        self.center = None
        self.edges = []
        self.network = self.set_network(num_edges)

    def set_network(self, length=1, loss=(0, 0)):
        network = Network("Star Network")
        self.edges = []
        center = Node('center',
                      qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                         {'sys_delay': 0, 'dead_time': 0}))
        nodes = [center]
        self.center = center
        for i in range(self.num_edges):
            node = Node(str(i),
                        qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                           {'sys_delay': 0, 'dead_time': 0}))
            nodes.append(node)
            self.edges.append(node)
        network.add_nodes(nodes)

        for i in range(self.num_edges):
            q_chan_out = generate_quantum_channel(name='center->' + str(i) + '_chan_quan',
                                                  length=length,
                                                  loss=loss)
            q_chan_in = generate_quantum_channel(name='center<-' + str(i) + '_chan_quan',
                                                 length=length,
                                                 loss=loss)
            network.add_connection(center,
                                   self.edges[i],
                                   label='center-' + str(i) + '_quan',
                                   channel_to=q_chan_out,
                                   channel_from=q_chan_in,
                                   port_name_node1='port_' + str(i) + '_quan',
                                   port_name_node2='center_quan'
                                   )
        return network


#--------------------------------------Line Topology-------------------------------------------------------

#Classical version
class LineTopology_c(_Topology):
    def __init__(self, num_nodes=5):
        super().__init__()
        self.num_nodes = num_nodes
        self.nodes = []
        self.network = self.set_network(num_nodes)

    def set_network(self, length=1, loss=(0, 0)):
        network = Network('Line Network')
        self.nodes = []
        for i in range(self.num_nodes):
            node = Node(str(i), qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                                   {'sys_delay': 0, 'dead_time': 0}))
            self.nodes.append(node)
            network.add_node(node)

        for i in range(self.num_nodes - 1):
            c_chan_out = generate_classical_channel(name=f'%s->%s_chan_cla' % (str(i), str(i + 1)),
                                                    length=length)
            c_chan_in = generate_classical_channel(name=f'%s<-%s_chan_cla' % (str(i), str(i + 1)),
                                                   length=length)
            network.add_connection(self.nodes[i],
                                   self.nodes[i + 1],
                                   label=f'%s-%s_cla' % (str(i), str(i + 1)),
                                   channel_to=c_chan_out,
                                   channel_from=c_chan_in,
                                   port_name_node1=f'port_%s%s_cla' % (i, i + 1),
                                   port_name_node2=f'port_%s%s_cla' % (i + 1, i)
                                   )
        return network


#Quantum version
class LineTopology_q(_Topology):
    def __init__(self, num_nodes=5):
        super().__init__()
        self.num_nodes = num_nodes
        self.nodes = []
        self.network = self.set_network(num_nodes)

    def set_network(self, length=1, loss=(0, 0)):
        network = Network('Line Network')
        self.nodes = []
        for i in range(self.num_nodes):
            node = Node(str(i), qmemory=_Topology.create_processor({'freq': 1e2, 'probs': (1, 0)},
                                                                   {'sys_delay': 0, 'dead_time': 0}))
            self.nodes.append(node)
            network.add_node(node)

        for i in range(self.num_nodes - 1):
            q_chan_out = generate_quantum_channel(name=f'%s->%s_chan_quan' % (str(i), str(i + 1)),
                                                  length=length,
                                                  loss=loss)
            q_chan_in = generate_quantum_channel(name=f'%s<-%s_chan_quan' % (str(i), str(i + 1)),
                                                 length=length,
                                                 loss=loss)

            network.add_connection(self.nodes[i],
                                   self.nodes[i + 1],
                                   label=f'%s-%s_quan' % (str(i), str(i + 1)),
                                   channel_to=q_chan_out,
                                   channel_from=q_chan_in,
                                   port_name_node1=f'port_%s%s_quan' % (i, i + 1),
                                   port_name_node2=f'port_%s%s_quan' % (i + 1, i)
                                   )
        return network


#--------------------------------------Line Topology-------------------------------------------------------

#Classical version
class CycleTopology_c(LineTopology_c):
    def __init__(self, num_nodes=5):
        super().__init__()
        self.num_nodes = num_nodes
        self.network = self.set_network()

    def set_network(self, length=1, loss=(0, 0)):
        # Just create a line network and connect the tail to the head
        self.nodes = []
        network = super().set_network(length, loss)

        c_chan_out = generate_classical_channel(name=f'%s->%s_chan_cla' % (str(self.num_nodes - 1), str(0)),
                                                length=length)
        c_chan_in = generate_classical_channel(name=f'%s<-%s_chan_cla' % (str(0), str(self.num_nodes - 1)),
                                               length=length)

        network.add_connection(self.nodes[self.num_nodes - 1],
                               self.nodes[0],
                               label=f'%s-%s_cla' % (str(self.num_nodes - 1), str(0)),
                               channel_to=c_chan_out,
                               channel_from=c_chan_in,
                               port_name_node1=f'port_%s%s_cla' % (str(self.num_nodes - 1), str(0)),
                               port_name_node2=f'port_%s%s_cla' % (str(0), str(self.num_nodes - 1)))
        return network


#Quantum version
class CycleTopology_q(LineTopology_q):
    def __init__(self, num_nodes=5):
        super().__init__()
        self.num_nodes = num_nodes
        self.network = self.set_network()

    def set_network(self, length=1, loss=(0, 0)):
        # Just create a line network and connect the tail to the head
        self.nodes = []
        network = super().set_network(length, loss)
        q_chan_out = generate_quantum_channel(name=f'%s->%s_chan_quan' % (str(self.num_nodes - 1), str(0)),
                                              length=length,
                                              loss=loss)
        q_chan_in = generate_quantum_channel(name=f'%s<-%s_chan_quan' % (str(0), str(self.num_nodes - 1)),
                                             length=length,
                                             loss=loss)

        network.add_connection(self.nodes[self.num_nodes - 1],
                               self.nodes[0],
                               label=f'%s-%s_quan' % (str(self.num_nodes - 1), str(0)),
                               channel_to=q_chan_out,
                               channel_from=q_chan_in,
                               port_name_node1=f'port_%s%s_quan' % (str(self.num_nodes - 1), str(0)),
                               port_name_node2=f'port_%s%s_quan' % (str(0), str(self.num_nodes - 1)))

        return network


#--------------------------------------Classical and quantum channel-------------------------------------------------------

def generate_quantum_channel(name, length=1000, loss=(0, 0)):
    error_models = {
        'delay_model': FibreDelayModel(length=length),
        'quantum_loss_model': FibreLossModel(p_loss_init=loss[0],
                                             p_loss_length=loss[1])
    }
    return QuantumChannel(name=name, models=error_models)


def generate_classical_channel(name, length=1000):
    return ClassicalChannel(name=name,
                            models={'delay_model': FibreDelayModel(length=length)})

def network(type,n_nodes,topology,node_distance): 
    available_types = ['quantum','classic']
    available_topologies = ['star_graph','grid_2d_graph','cycle_graph','line_graph']

    #-------------------------set inputs-----------------------

    if type == 'quantum':
        for to in available_topologies:
            if topology == 'star_graph':
                starq = StarTopology_q()
                network = starq.set_network()
            elif topology == 'grid_2d_graph':
                gridq = GridTopology_q()
                network = gridq.set_network()
            elif topology == 'cycle_graph':
                cycleq = CycleTopology_q()
                network = cycleq.set_network()
            elif topology == 'line_graph':
                lineq = LineTopology_q()
                network = lineq.set_network()

    elif type == 'classic':
        for to in available_topologies:
            if topology == 'star_graph':
                starc = StarTopology_c()
                network = starc.set_network()
            elif topology == 'grid_2d_graph':
                gridc = GridTopology_c()
                network = gridc.set_network()
            elif topology == 'cycle_graph':
                cyclec = CycleTopology_c()
                network = cyclec.set_network()
            elif topology == 'line_graph':
                linec = LineTopology_c()
                network = linec.set_network()

    #print("chose and set up topology")
        
    #-------------------------generate netsquid network-----------------------

    nodes = []
    for i in range(n_nodes):
        node = Node(f"node_{i}", qmemory= processor(depolar_rate = 0, dephase_rate = 0)) #ideal case for now
        node.number = i
        nodes.append(node)
    
    network.add_nodes(nodes)

    """
    #Testing
    print(network)
    print(network.nodes)
    print(network.connections)
    """

    """  
    print("set up network")
    print("n_nodes:",n_nodes)
    for i in range(0,n_nodes):
        j = i + 1
        print("j:",j)
        print("i:",i)

        while j <= n_nodes:
    
            #print("started filling networks")
            if type == 'quantum':
                print("creating a quantum network")
                source_frequency = 4e4 #arbitrartly set right now
                #setting type of connection
                q_conn = QuantumConnection(name=f'ent_conn_{i}{j}',
                                        length=node_distance,
                                        source_frequency=source_frequency)
                #adding connection to the network
                network.add_connection(nodes[i],
                                       nodes[j],
                                       label=f'qonn_{i}{j}',
                                       connection=q_conn,
                                       port_name_node1=f'qla_%s' % j,
                                       port_name_node2=f'qla_%s' % i)
                
                port_1, port_2 = network.add_connection(nodes[i], nodes[j], connection=q_conn, label=f"quan_%s%s" % (i, j),
                                                        port_name_node1=f"qin_ent_source_{i}{j}", port_name_node2=f"qin_ent_source_{i}{j}")
            
                nodes[i].ports[port_1].forward_input(nodes[i].qmemory.ports[f'qin{j}'])
                nodes[j].ports[port_2].forward_input(nodes[j].qmemory.ports[f'qin{i}'])
                
                j += 1

            else:
                print("doing classical network")
                c_conn = ClassicalConnection(name=f'c_conn_{i}{j}',
                                                length=node_distance)
                network.add_connection(nodes[i],
                        nodes[j],
                        label=f'conn_{i}{j}',
                        connection=c_conn,
                        port_name_node1=f'cla_%s' % j,
                        port_name_node2=f'cla_%s' % i)
                
                port_1, port_2 = network.add_connection(
                                nodes[i], nodes[j], connection=q_conn, label=f"cuan_%s%s" % (i, j),
                                port_name_node1=f"cin_ent_source_{i}{j}", port_name_node2=f"cin_ent_source_{i}{j}")
                
                nodes[i].ports[port_1].forward_input(nodes[i].qmemory.ports[f'cin{j}'])
                nodes[j].ports[port_2].forward_input(nodes[j].qmemory.ports[f'cin{i}'])
                
                j += 1
        """                                    

        #network.type = type
    
    #-------------------------return network-----------------------
    
    return network

class Initiatesystem(NodeProtocol):

    def __init__(self, node, num_qubits=100):
        super().__init__(node)
        self.num_qubits = num_qubits

    def run(self):
        for _ in range(self.num_qubits):
            q = ns.qubits.create_qubits(1) 
            self.send_signal(Signals.SUCCESS, 2) 
            self.node.qmemory.put(q, 0, replace=True) 
            yield self.await_timer(100) 


class Sendmessage(NodeProtocol):

    def run(self):
        def forward(message):

            self.send_signal(Signals.SUCCESS, 1)
            qubit = message.items[0]
            operate(qubit, ops.H)
            
            if 'rx_port_name' in message.meta:
                port = 1 if message.meta['rx_port_name'] == 'qua_p1' else 0
            else:
                port = 0
            
            self.node.y[port] = qubit.qstate.qrepr.ket
            self.node.x[port] = lr * self.node.x[port] + (1 - lr)
            self.node.x[1 - port] = lr * self.node.x[1 - port]
            

            p = np.random.random()            
            if np.random.random() < p:
                ns.qubits.qubitapi.assign_qstate([qubit], np.array([w[0], w[2]]) / sqrt(p))
                final_port = 0
            else:
                ns.qubits.qubitapi.assign_qstate([qubit], np.array([w[1], w[3]]) / sqrt(1 - p))
                final_port = 1

            self.node.ports[f'qua_{final_port}'].tx_output(message)
        
        self.node.qmemory.ports['qout'].bind_output_handler(forward)
        if 'qua_p' in self.node.ports:
            self.node.ports['qua_p'].bind_input_handler(forward)
        if 'qua_p1' in self.node.ports:
            self.node.ports['qua_p1'].bind_input_handler(forward, tag_meta=True)
        if 'qua_p2' in self.node.ports:
            self.node.ports['qua_p2'].bind_input_handler(forward, tag_meta=True)

        while True:
            if 'qua_p' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p'])
            elif 'qua_p1' in self.node.ports and 'qua_p2' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p1']) | self.await_port_input(
                    self.node.ports['qua_p2'])
            elif 'qua_p1' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p1'])
            elif 'qua_p2' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p2'])
            else:
                yield self.await_port_input(self.node.qmemory.ports['qin'])
                self.node.qmemory.pop(0)


class Readmessage(NodeProtocol):

    def run(self):
        def measure(message):

            self.send_signal(Signals.SUCCESS, (self.node.number, 0))
        if 'qua_p' in self.node.ports:
            self.node.ports['qua_p'].bind_input_handler(measure) 
        if 'qua_p1' in self.node.ports:
            self.node.ports['qua_p1'].bind_input_handler(measure)
        if 'qua_p2' in self.node.ports:
            self.node.ports['qua_p2'].bind_input_handler(measure)

        while True:
            if 'qua_p' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p'])
            elif 'qua_p1' in self.node.ports and 'qua_p2' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p1']) | self.await_port_input(
                    self.node.ports['qua_p2'])
            elif 'qua_p1' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p1'])
            elif 'qua_p2' in self.node.ports:
                yield self.await_port_input(self.node.ports['qua_p2'])
            else:
                yield self.await_port_input(self.node.qmemory.ports['qin'])
                self.node.qmemory.pop(0)

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

    #print("network experiment main initiate")

    network1 = network('quantum',nodes,t_topology,n_distance) #,noise_model)
    #network2 = network('classic',nodes,t_topology,n_distance) #noise_model)

    #print("set networks initiate")
    #------------------------- run network 1 -----------------------

    #Append protocols to nodes
    protocols = []
    i = 0
    for node in network1.nodes:
        i = i+1
        #initiating communications protocols
        protocols.append(Initiatesystem(network1.nodes[node]))
        
        """
        if network1.type == 'quantum': #with entanglement
            if i <= nodes:
                protocols.append(EntangleNodes(node = node,role = "source", name = "A"))
                protocols.append(EntangleNodes(node = node+1,role = "receiver",name = "B"))
        """
        #print("sending message")
        protocols.append(Sendmessage(network1.nodes[node]))
        #print("message sent")

        #read message
        protocols.append(Readmessage(network1.nodes[node]))

    #------------------------- collect the data -----------------------
    #print("collect data initiate")
    qubits_received_stats = {}
    qubit_paths = {}
    current_qubit = 0

    def collect_stats(evexpr):
        print("Collecting Signals")
        trigger = evexpr.triggered_events[-1].source
        print("Events 1: ", evexpr)
        print("Triggers: ",trigger)
        print("Signals: ",trigger.get_signal_result(Signals.SUCCESS))
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

    #print(dc)
    dc = DataCollector(collect_stats)
    print("Data Collector",dc)

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