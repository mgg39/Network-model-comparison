import netsquid.components.instructions as instr
import netsquid.qubits.ketstates as ks
from netsquid.components import QuantumChannel, ClassicalChannel, FibreDelayModel, QSource, SourceStatus, \
    FibreLossModel, QuantumDetector, FixedDelayModel
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.nodes import Node, Network
from netsquid.qubits import StateSampler, operators as ops

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
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False),
            PhysicalInstruction(instr.INSTR_X, duration=1, parallel=False),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False),
            PhysicalInstruction(instr.INSTR_CNOT, duration=5, parallel=False)
        ]

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


class GridTopology(_Topology):
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
            c_chan_out = generate_classical_channel(name='%d%d_%d%d_chan_cla' % (i1, j1, i2, j2),
                                                    length=length)
            c_chan_in = generate_classical_channel(name='%d%d_%d%d_chan_cla' % (i2, j2, i1, j1),
                                                   length=length)
            return [q_chan_out, q_chan_in, c_chan_out, c_chan_in]

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
                    network.add_connection(self.nodes[i][j],
                                           self.nodes[link[0]][link[1]],
                                           label='%d%d_%d%d_cla_chan',
                                           channel_to=channels[2],
                                           channel_from=channels[3],
                                           port_name_node1=f'port_%d%d_cla' % (link[0], link[1]),
                                           port_name_node2=f'port_%d%d_cla' % (i, j)
                                           )
        return network


class StarTopology(_Topology):
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

            c_chan_out = generate_classical_channel(name='center->' + str(i) + '_chan_cla',
                                                    length=length)
            c_chan_in = generate_classical_channel(name='center<-' + str(i) + '_chan_cla',
                                                   length=length)
            network.add_connection(center,
                                   self.edges[i],
                                   label='center-' + str(i) + '_quan',
                                   channel_to=q_chan_out,
                                   channel_from=q_chan_in,
                                   port_name_node1='port_' + str(i) + '_quan',
                                   port_name_node2='center_quan'
                                   )
            network.add_connection(center,
                                   self.edges[i],
                                   label='center-' + str(i) + '_cla',
                                   channel_to=c_chan_out,
                                   channel_from=c_chan_in,
                                   port_name_node1='port_' + str(i) + '_cla',
                                   port_name_node2='center_cla'
                                   )
        return network


class LineTopology(_Topology):
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
            c_chan_out = generate_classical_channel(name=f'%s->%s_chan_cla' % (str(i), str(i + 1)),
                                                    length=length)
            c_chan_in = generate_classical_channel(name=f'%s<-%s_chan_cla' % (str(i), str(i + 1)),
                                                   length=length)
            network.add_connection(self.nodes[i],
                                   self.nodes[i + 1],
                                   label=f'%s-%s_quan' % (str(i), str(i + 1)),
                                   channel_to=q_chan_out,
                                   channel_from=q_chan_in,
                                   port_name_node1=f'port_%s%s_quan' % (i, i + 1),
                                   port_name_node2=f'port_%s%s_quan' % (i + 1, i)
                                   )
            network.add_connection(self.nodes[i],
                                   self.nodes[i + 1],
                                   label=f'%s-%s_cla' % (str(i), str(i + 1)),
                                   channel_to=c_chan_out,
                                   channel_from=c_chan_in,
                                   port_name_node1=f'port_%s%s_cla' % (i, i + 1),
                                   port_name_node2=f'port_%s%s_cla' % (i + 1, i)
                                   )
        return network


class CycleTopology(LineTopology):
    def __init__(self, num_nodes=5):
        super().__init__()
        self.num_nodes = num_nodes
        self.network = self.set_network()

    def set_network(self, length=1, loss=(0, 0)):
        self.nodes = []
        network = super().set_network(length, loss)
        q_chan_out = generate_quantum_channel(name=f'%s->%s_chan_quan' % (str(self.num_nodes - 1), str(0)),
                                              length=length,
                                              loss=loss)
        q_chan_in = generate_quantum_channel(name=f'%s<-%s_chan_quan' % (str(0), str(self.num_nodes - 1)),
                                             length=length,
                                             loss=loss)
        c_chan_out = generate_classical_channel(name=f'%s->%s_chan_cla' % (str(self.num_nodes - 1), str(0)),
                                                length=length)
        c_chan_in = generate_classical_channel(name=f'%s<-%s_chan_cla' % (str(0), str(self.num_nodes - 1)),
                                               length=length)
        network.add_connection(self.nodes[self.num_nodes - 1],
                               self.nodes[0],
                               label=f'%s-%s_quan' % (str(self.num_nodes - 1), str(0)),
                               channel_to=q_chan_out,
                               channel_from=q_chan_in,
                               port_name_node1=f'port_%s%s_quan' % (str(self.num_nodes - 1), str(0)),
                               port_name_node2=f'port_%s%s_quan' % (str(0), str(self.num_nodes - 1)))
        network.add_connection(self.nodes[self.num_nodes - 1],
                               self.nodes[0],
                               label=f'%s-%s_cla' % (str(self.num_nodes - 1), str(0)),
                               channel_to=c_chan_out,
                               channel_from=c_chan_in,
                               port_name_node1=f'port_%s%s_cla' % (str(self.num_nodes - 1), str(0)),
                               port_name_node2=f'port_%s%s_cla' % (str(0), str(self.num_nodes - 1)))
        return network


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