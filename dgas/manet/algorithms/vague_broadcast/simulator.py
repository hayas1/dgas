from __future__ import annotations
from typing import Tuple, Type, Dict
import json
import datetime as dt
import os

import torch
import matplotlib.pyplot as plt
import matplotlib.animation as anm


from dgas import rc, node, edge, message, graph, result, daemon, plot
from dgas.manet import collider, physics, field


class BroadcastFieldRecord(result.FieldRecord):
    def __init__(self):
        super().__init__()
        self.frame = 0


class BroadcastLoggingField(field.LoggingGravityField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        self.rootnode = [n for n in g.nodes() if n.is_root][0]
        self.record = BroadcastFieldRecord()

    def update(self, t):
        self.record.frame = t
        return super().update(t)


class BroadcastNodeRecord(result.NodeRecord):
    def __init__(self, identifier: rc.NodeID):
        super().__init__(identifier)
        self.broadcasted_frame = -1
        self.number_of_sended = 0
        self.number_of_received = 0

    def to_dict(self) -> Dict[str, Union[rc.GlobalTime, MessageRecord.DictType]]:
        d = super().to_dict()
        d.update({rc.key_broadcasted_frame_log: self.broadcasted_frame,
                  rc.key_number_of_sended_log: self.number_of_sended})
        return d


class BroadcastNode(node.LoggingNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)
        self.record = BroadcastNodeRecord(identifier)
        self.oracle_sendable = set()
        self.received = False
        self.sended = False
        self.sended_frame = None
        self.received_message = None

    def is_root(self):
        return self.identifier == 0

    def oracle_broadcast(self, msg: rc.MessageType):
        to = set(self.neighbors()) & self.oracle_sendable
        self.broadcast_to(msg, to)
        self.sended = True
        self.record.broadcasted_frame = self.record.frame
        self.record.number_of_sended += len(to)

    def update(self, t: rc.GlobalTime):
        if t == 0 and self.is_root():
            self.on_receive('msg')     # if message receive, send message later
            self.drawable().color = rc.root_color
            self.record.number_of_received -= 1
        if t == self.sended_frame:
            self.oracle_broadcast(self.received_message)
        return super().update(t)

    def on_receive(self, msg: rc.MessageType):
        self.received = True
        self.record.number_of_received += 1
        if not self.sended:
            self.sended_frame = self.record.frame + rc.node_delay
            self.received_message = msg
        if not self.is_root():
            self.drawable().color = rc.broadcasted_color


class BroadcastSimulator:
    def __init__(self, algorithm: str, n: int, xlen: rc.Number, ylen: rc.Number,
                 node_class: Type[BroadcastNode] = None,
                 field_class: Type[BroadcastLoggingField] = None,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        self.algorithm = algorithm
        self.daemon = daemon.ManetDaemon(
            field.init_random(n, xlen, ylen, node_class, field_class))
        self.untiltime = untiltime
        self.timeout = timeout
        self.condition_end = conditionend
        self.id_draw = identifierdraw
        self.edge_draw = edgedraw
        self.message_draw = messagedraw
        self.kwargs = kwargs

    def nodes(self) -> List[BroadcastNode]:
        return self.daemon.graph.nodes()

    def messages(self) -> List[message.Message]:
        return self.daemon.graph.messages()

    def field(self) -> BroadcastLoggingField:
        return self.daemon.field

    def succeed(self, nomessage=True) -> bool:
        broadcasted = all(node.received for node in self.nodes())
        return broadcasted

    def convergence(self) -> bool:
        return all(node.sended == node.received for node in self.nodes())

    def failed(self) -> bool:
        return self.convergence() and not self.success()

    def connectivity(self) -> List[bool]:
        return all(self.daemon.field.record.connectivity)

    def convergence_frame(self) -> rc.GlobalTime:
        return max(max([mr.frame for mr in node.record.received_message], default=0)
                   for node in self.nodes())

    def number_of_sended_messages(self) -> int:
        return sum(node.record.number_of_sended for node in self.nodes())

    def number_of_sended_nodes(self) -> int:
        return sum(node.record.number_of_sended > 0 for node in self.nodes())

    def number_of_received_messages(self) -> int:
        return sum(node.record.number_of_received for node in self.nodes())

    def number_of_received_nodes(self) -> int:
        return sum(node.record.number_of_received > 0 for node in self.nodes())

    def sended_nodes_per_whole(self) -> float:
        return self.number_of_sended_nodes() / len(self.nodes())

    def received_nodes_per_whole(self) -> float:
        return self.number_of_received_nodes() / len(self.nodes())

    def whole_result_dict(self) -> Dict[str, Any]:
        return {rc.key_result_algorithm: self.algorithm,
                rc.key_result_number_of_nodes: len(self.nodes()),
                rc.key_result_simulate_terminate_frame: self.field().record.frame,
                rc.key_result_delay: rc.node_delay,
                rc.key_result_all_sended_messages: self.number_of_sended_messages(),
                rc.key_result_all_received_messages: self.number_of_received_messages(),
                rc.key_result_all_sended_nodes: self.number_of_sended_nodes(),
                rc.key_result_all_sended_nodes_per_whole: self.sended_nodes_per_whole(),
                rc.key_result_all_received_nodes: self.number_of_received_nodes(),
                rc.key_result_all_received_nodes_per_whole: self.received_nodes_per_whole(),
                rc.key_result_connectivity: self.connectivity(),
                rc.key_result_convergence: self.convergence(),
                rc.key_result_convergence_frame: self.convergence_frame(),
                rc.key_result_success: self.succeed()}

    def animate(self, **kwargs) -> anm.ArtistAnimation:
        if self.timeout == None and self.untiltime == None and not self.condition_end:
            raise ValueError(
                'no timeout and untiltime and convergence cause of infinite loop.')
        elif self.condition_end:
            return plot.artistanimate_manet_daemon(
                self.daemon, identifier=self.id_draw,
                edge=self.edge_draw, message=self.message_draw,
                untiltime=self.untiltime, timeout=self.timeout,
                condition=lambda x: x.convergence() or not x.connectivity(), arg=self,
                **self.kwargs, **kwargs)
        else:
            return plot.artistanimate_manet_daemon(
                self.daemon, identifier=self.id_draw,
                edge=self.edge_draw, message=self.message_draw,
                untiltime=self.untiltime, timeout=self.timeout, **self.kwargs, **kwargs)

    def simulate(self):
        if self.timeout == None and self.untiltime == None and not self.condition_end:
            raise ValueError(
                'no timeout and untiltime and convergence cause of infinite loop.')
        elif self.condition_end:
            self.daemon.main_loop(untiltime=self.untiltime, timeout=self.timeout,
                                  condition=lambda x: x.convergence() or not x.connectivity(),
                                  arg=self)
        else:
            self.daemon.main_loop(untiltime=self.untiltime,
                                  timeout=self.timeout)

    def result_dict(self) -> Dict[str, Any]:
        whole_result = self.whole_result_dict()
        # graph_result = self.field().graph.record.to_dict()
        field_result = self.field().record.to_dict()
        nodes_result = [node.record.to_dict() for node in self.nodes()]
        return {rc.key_whole_result: whole_result,
                # rc.key_graph_result: graph_result,
                rc.key_field_result: field_result,
                rc.key_nodes_result: nodes_result}

    def make_dirname(self, dirname: str = None):
        ts = hex(int(dt.datetime.now().timestamp()*10**6))
        # now = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        dirname = dirname or f'{self.algorithm}{len(self.nodes())}nodes{ts}'
        return dirname

    def save_as_json(self, dirpath: str, dirname: str = None, mkdir=False):
        dirname = self.make_dirname(dirname)
        jsondir = os.path.join(dirpath, dirname)
        os.makedirs(jsondir, exist_ok=mkdir)
        for resulttype, resultjson in self.result_dict().items():
            with open(os.path.join(jsondir, resulttype + '.json'), 'w') as f:
                json.dump(resultjson, f, indent=4)

    def run_and_save(self, dirpath: str, dirname: str = None, ani=False, mkdir=False,
                     connectedonly=False) -> Union[None, str]:
        if ani:
            anm = self.animate(interval=1000/30)
        else:
            self.simulate()
        if self.connectivity() or not connectedonly:
            dirname = self.make_dirname(dirname)
            resultdir = os.path.join(dirpath, dirname)
            os.makedirs(resultdir, exist_ok=mkdir)
            self.save_as_json(dirpath, dirname, mkdir=mkdir)
            if ani:
                anm.save(os.path.join(resultdir, rc.animation_filename),
                         writer='pillow')
            return resultdir
