import numpy as np
from numpy import sqrt
from numpy.random import rand

import netsquid as ns
from netsquid.nodes import Node, Network
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.qubits import operators as ops
from netsquid.protocols import NodeProtocol
from netsquid.protocols import Signals
from netsquid.protocols import Protocol, ServiceProtocol
from netsquid.components.component import Message 
from netsquid.components.instructions import *
from netsquid.components.qprogram import QuantumProgram
from netsquid.components.instructions import Instruction 
from netsquid.examples.simple_link import abc,namedtuple,deque

class NetworkProtocol(Protocol):
    """Send requests to an EG service protocol.

    Will automatically stop the services and their sub-protocols
    when the requests are finished.

    Parameters
    ----------
    name : str
        Name to identify this protocol.
    entangle_protocol : :class:`~netsquid.examples.simple_link.EGService`
        The service that will get the requests from this network.
    remote_entangle_protocol : :class:`~netsquid.examples.simple_link.EGService`
       The service that will create the pairs together with the entangle_protocol.

    """

    def __init__(self, name, entangle_protocol, remote_entangle_protocol):
        super().__init__(name=name)
        self.add_subprotocol(entangle_protocol, "EGP_Alice")
        self.add_subprotocol(remote_entangle_protocol, "EGP_Bob")

    def run(self):
        """Start the protocols and put requests to Alice."""
        proto = self.subprotocols['EGP_Alice'].start()
        self.subprotocols['EGP_Bob'].start()
        # Start with a single request
        req_1 = proto.req_create(purpose_id=4, number=3)
        create_id = proto.put(req_1)['create_id']
        print(f"Waiting for responses with create_id {create_id}")
        yield from self.show_results(proto, req_1)
        req_2 = proto.req_create(purpose_id=6, number=2)
        create_id = proto.put(req_2)['create_id']
        print(f"Waiting for responses with create_id {create_id}")
        req_3 = proto.req_create(purpose_id=4, number=1)
        create_id = proto.put(req_3)['create_id']
        print(f"Waiting for responses with create_id {create_id}")
        yield from self.show_results(proto, req_2)
        yield from self.show_results(proto, req_3)
        print('Finished all network requests')

    def show_results(self, proto, request):
        """ Show the qubits which are entangled as a result of the request.

        Parameters
        ----------
        proto : :class:`~netsquid.examples.simple_link.EGProtocol`
            The entanglement generation service
        request : :class:`~netsquid.examples.simple_link.EGService.req_create`
            The request

        Yields
        ------
        :class:`~pydynaa.core.EventExpression`
            The eventexpressions required to wait for the response signals.

        """
        ok_signal = proto.get_name(proto.res_ok)
        print(f"Qubits between Alice and Bob with purpose_id {request.purpose_id}:")
        for _ in range(request.number):
            yield self.await_signal(proto, ok_signal)
            res = proto.get_signal_result(ok_signal, self)
            qubits = proto.node.qmemory.peek(res.logical_qubit_id)[0].qstate.qubits
            print(f"  {ns.sim_time():8.0f}: {qubits} with create_id {res.create_id}")

class MidpointHeraldingProtocol(NodeProtocol):
    """Attempt to generate entanglement via a HeraldingConnection.

    This protocol sends a trigger to an EGProtocol every ``time_step`` nanoseconds.
    On a response the protocol creates a qubit in memory, entangles it with a photon,
    and sends this photon to the qout port of the quantum memory.
    This port is expected to forward the photon to the heralded connection.
    This connection is expected to return an outcome of the photon measurement,
    which returns 1 or 2 (each denotes an entangled state) for success.
    The photon will be generated on position 0, and the qubits on 1 .. N.

    Parameters
    ----------
    node : `~netsquid.nodes.node.Node`
        The node this protocol runs on.
    time_step : int
        The period of the triggers in nanoseconds.
    q_port_name : str
        The name of the port connected to the heraled connection.

    Attributes
    ----------
    trigger_label : str
        The label of the trigger signal
    answer_label : str
        The label of the answer signal

    """

    def __init__(self, node, time_step, q_port_name):
        super().__init__(node=node)
        self.time_step = time_step
        self.node.qmemory.ports['qout'].forward_output(self.node.ports[q_port_name])
        # And we will wait for an outcome on the input port
        self.port_name = q_port_name
        self.q_port_name = q_port_name
        # We have to remember if we already send a photon
        self.trigger_label = "TRIGGER"
        self.answer_label = "ANSWER"
        self.add_signal(self.trigger_label)
        self.add_signal(self.answer_label)
        self._do_task_label = 'do_task_label'
        self.add_signal(self._do_task_label)

    class EmitProgram(QuantumProgram):
        """Program to create a qubit and emit an entangled photon to the 'qout' port.

        """

        def __init__(self):
            super().__init__(num_qubits=2)

        def program(self):
            # Emit from q2 using q1
            q1, q2 = self.get_qubit_indices(self.num_qubits)
            self.apply(INSTR_INIT, q1)
            self.apply(INSTR_EMIT, [q1, q2])
            yield self.run()

    def run(self):
        """Sends triggers periodically or starts an entanglement attempt.

        The triggers are skipped during the entanglement attempt for simplicity.

        Yields
        ------
        :class:`~pydynaa.core.EventExpression`
            Await a timer signal or a response from the connection.

        """
        while True:
            #  Instead of a duration we specify the time explicitly
            #  to be a mulitple of the time_step.
            time = (1 + (ns.sim_time() // self.time_step)) * self.time_step
            wait_timer = self.await_timer(end_time=time)
            wait_signal = self.await_signal(self, self._do_task_label)
            evexpr = yield wait_timer | wait_signal
            if evexpr.second_term.value:
                # Start the entanglement attempt
                qpos = self.get_signal_result(self._do_task_label)
                prog = self.EmitProgram()
                self.node.qmemory.execute_program(prog, qubit_mapping=[qpos + 1, 0])
                port = self.node.ports[self.q_port_name]
                yield self.await_port_input(port)
                message = port.rx_input()
                if message.meta.get("header") == 'photonoutcome':
                    outcome = message.items[0]
                else:
                    outcome = 'FAIL'
                self.send_signal(self.answer_label, result=(outcome, qpos + 1))
            else:
                self.send_signal(self.trigger_label)

    def do_task(self, qpos):
        """Start the task.

        Parameters
        ----------
        qpos : int
            The number indicating which qubit pair we are making.

        """
        self.send_signal(self._do_task_label, result=qpos)


class EGService(ServiceProtocol, metaclass= abc.ABCMeta):
    """Abstract interface for an Entanglement Generation Service.

    Defines the available request and response types, and implements the queue mechanism.
    Every request will be assigned a unique create_id, which is
    returned when a request is put to this service.

    Parameters
    ----------
    node : :class:`~netsquid.nodes.node.Node`
        The node this protocol runs on.
    name : str, optional
        The name of this protocol. Default EGService.

    Attributes
    ----------
    req_create : namedtuple
        A request to create entanglement with a remote node.
    res_ok : namedtuple
        A response to indicate a create request has finished.

    """

    # Define the requests and responses as class attributes so
    # they are identical for every EGProtocol instance
    req_create = namedtuple('LinkLayerCreate', ['purpose_id', 'number'])
    res_ok = namedtuple('LinkLayerOk', ['purpose_id', 'create_id', 'logical_qubit_id'])

    def __init__(self, node, name=None):
        super().__init__(node=node, name=name)
        # Register the request and response
        self.register_request(self.req_create, self.create)
        self.register_response(self.res_ok)
        # We will use a queue for requests
        self.queue = deque()
        self._new_req_signal = "New request in queue"
        self.add_signal(self._new_req_signal)
        self._create_id = 0

    def handle_request(self, request, identifier, start_time=None, **kwargs):
        """Schedule the request on the queue.

        Schedule the request in a queue and
        signal to :meth:`~netsquid.examples.simple_link.EGProtocol.run`
        new items have been put into the queue.

        Parameters
        ----------
        request :
            The object representing the request.
        identifier : str
            The identifier for this request.
        start_time : float, optional
            The time at which the request can be executed. Default current simulation time.
        kwargs : dict, optional
            Additional arguments which can be set by the service.

        Returns
        -------
        dict
            The dictionary with additional arguments.

        Notes
        -----
        This method is called after
        :meth:`~netsquid.protocols.serviceprotocol.ServiceProtocol.put` which
        does the type checking etc.

        """
        if start_time is None:
            start_time = ns.sim_time()
        self.queue.append((start_time, (identifier, request, kwargs)))
        self.send_signal(self._new_req_signal)
        return kwargs

    def run(self):
        """Wait for a new request signal, then run the requests one by one.

        Assumes request handlers are generators and not functions.

        """
        while True:
            yield self.await_signal(self, self._new_req_signal)
            while len(self.queue) > 0:
                start_time, (handler_id, request, kwargs) = self.queue.popleft()
                if start_time > ns.sim_time():
                    yield self.await_timer(end_time=start_time)
                func = self.request_handlers[handler_id]
                args = request._asdict()
                gen = func(**{**args, **kwargs})
                yield from gen

    def _get_next_create_id(self):
        # Return a unique create id.
        self._create_id += 1
        return self._create_id

    @abc.abstractmethod
    def create(self, purpose_id, number, create_id, **kwargs):
        """Implement the entanglement generation.

        Parameters
        ----------
        purpose_id : int
            Integer representing which purpose this entanglement is for.
            Used to communicate to the higher layers.
        number : int
            Number of qubit pairs to make.
        create_id : int
            The unique identifier provided by the service.
        kwargs : dict, optional
            Drain for any optional parameters.

        """
        pass

class EGProtocol(EGService):
    """Implement an Entanglement Generation service.

    Upon a *LinkLayerCreate* request generates pairs of entangled qubits, of which one
    is locally stored and the other is stored at the remote node.
    Requests are fulfulled in FIFO order, and upon completion
    a response signal is sent.

    Parameters
    ----------
    node : :class:`~netsquid.nodes.node.Node`
        The node this protocol runs on.
    c_port_name : str
        The name of the port which is connected to the remote node.
    name : str, optional
        The name of this protocol. Default EGProtocol.

    """

    def __init__(self, node, c_port_name, name=None):
        super().__init__(node=node, name=name)
        # Require a Physical Layer protocol
        self._mh_name = "MH_Protocol"
        # Setup queue synchronization
        self.c_port = self.node.ports[c_port_name]
        self.c_port.bind_input_handler(self._handle_msg)

    def add_phys_layer(self, mh_protocol):
        """Add a physical layer protocol as a subprotocol.

        Parameters
        ----------
        mh_protocol :
            The protocol which implements a physical layer.

        """
        self.add_subprotocol(mh_protocol, name=self._mh_name)

    def handle_request(self, request, identifier, start_time=None, **kwargs):
        """Synchronize the request with the other service and schedule it on the queue.

        Parameters
        ----------
        request :
            The object representing the request.
        identifier : str
            The identifier for this request.
        start_time : float, optional
            The time at which the request can be executed. Default current time.
        kwargs : dict, optional
            Additional arguments not part of the original request.

        Returns
        -------
        dict
            The dictionary with additional arguments.
            For the create request this is the unique create id.

        """
        if kwargs.get('create_id') is None:
            kwargs['create_id'] = self._get_next_create_id()
        if start_time is None:
            travel_time = 10000
            start_time = ns.sim_time() + travel_time
            # Make sure Message don't combine by specifying a header.
            self.c_port.tx_output(
                Message([request, identifier, start_time, kwargs], header=request)
            )
        return super().handle_request(request, identifier, start_time, **kwargs)

    def _handle_msg(self, msg):
        """Handle incoming messages from the other service.

        The services use these messages to ensure they start
        the same request at the same time.

        Parameters
        ----------
        msg : Message
            A Message from another ServiceProtocol containing request
            and scheduling data.

        """
        request, handler_id, start_time, kwargs = msg.items
        self.handle_request(request, handler_id, start_time, **kwargs)

    def run(self):
        """Make sure we have an subprotocol before running our program.

        """
        if self._mh_name not in self.subprotocols or \
                not isinstance(self.subprotocols[self._mh_name], Protocol):
            raise ValueError("EGProtocol requires a physical layer protocol to be added.")
        self.start_subprotocols()
        yield from super().run()

    def create(self, purpose_id, number, **kwargs):
        """Handler for create requests.

        Create qubits together with a remote node.

        Parameters
        ----------
        purpose_id : int
            The number used to to tag this request for a specific purpose in a higher layer.
        number : int
            The number of qubits to make in this request.

        Yields
        ------
        :class:`~pydynaa.core.EventExpression`
            The expressions required to execute the create request.

        Returns
        -------
        :obj:`~netsquid.examples.simple_link.EGProtocol.res_ok`
            The response object indicating we successfully made the requested qubits.

        """
        create_id = kwargs['create_id']
        self._create_id = create_id
        curpairs = 0
        sub_proto = self.subprotocols[self._mh_name]
        wait_trigger = self.await_signal(sub_proto, sub_proto.trigger_label)
        wait_answer = self.await_signal(sub_proto, sub_proto.answer_label)
        # Start the main loop
        while curpairs < number:
            evexpr = yield wait_trigger | wait_answer
            for event in evexpr.triggered_events:
                qpos = self._handle_event(event, curpairs)
                if qpos is not None:
                    response = self.res_ok(purpose_id, create_id, qpos)
                    self.send_response(response)
                    curpairs += 1

    def _handle_event(self, event, curpairs):
        # Communicate with the physical layer on trigger and answers signals.
        sub_proto = self.subprotocols[self._mh_name]
        label, value = sub_proto.get_signal_by_event(event, receiver=self)
        if label == sub_proto.trigger_label:
            sub_proto.do_task(qpos=curpairs)
        elif label == sub_proto.answer_label:
            outcome, qpos = value
            # outcome of 1 is |01>+|10>, 2 is |01>-|10>.
            # Other outcomes are non-entangled states.
            if outcome == 1 or outcome == 2:
                return qpos
        return None

def setup_protocol(network):
    """Configure the protocols.

    Parameters
    ----------
    network : :class:`~netsquid.nodes.network.Network`
        The network to configure the protocols on. Should consist of two nodes
        called Alice and Bob.

    Returns
    -------
    :class:`~netsquid.protocols.protocol.Protocol`
        A protocol describing the complete simple link setup.

    """
    nodes = network.nodes
    # Setup Alice
    q_ports = network.get_connected_ports(*nodes, label='quantum')
    c_ports = network.get_connected_ports(*nodes, label='classical')
    alice_mhp = MidpointHeraldingProtocol(nodes['Alice'], 500, q_ports[0])
    alice_egp = EGProtocol(nodes['Alice'], c_ports[0])
    alice_egp.add_phys_layer(alice_mhp)
    # Setup Bob
    bob_mhp = MidpointHeraldingProtocol(nodes['Bob'], 470, q_ports[1])
    bob_egp = EGProtocol(nodes['Bob'], c_ports[1])
    bob_egp.add_phys_layer(bob_mhp)
    return NetworkProtocol("SimpleLinkProtocol", alice_egp, bob_egp)