from __future__ import annotations
from typing import NewType, Union, List, Tuple, Sequence, Callable, Any

import matplotlib.animation as anm

from dgas import rc, node, message, graph, time, plot
from dgas.manet import field


class FairDaemon:
    def __init__(self, g: graph.GraphType):
        self.graph = g

    def choose(self) -> Tuple[List[node.Node], List[message.Message]]:
        return self.graph.nodes(), self.graph.messages()

    def update_nodes(self, t: rc.GlobalTime, nodelist: Sequence[node.Node] = None):
        for node in nodelist or self.graph.nodes():
            if not node.clashed:
                node.update(t)

    def update_messages(self, t: rc.GlobalTime, messagelist: Sequence[message.Message] = None):
        for message in messagelist or self.graph.messages():
            message.update(t)
        arrive = {nod: {msg for msg in msgs if msg.arrive()}
                  for (nod, msgs) in self.graph.sendings.items()}
        for nod, arrived in arrive.items():
            self.graph.remove_messages_from_node(nod, arrived)
            for msg in arrived:
                msg.to_node.receive(msg.from_node, msg.raw)

    def each_loop(self, t: rc.GlobalTime):
        nodes, messages = self.choose()
        self.update_nodes(t, nodes)
        self.update_messages(t, messages)

    def main_loop(self, untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None,
                  condition: Callable[[Any], bool] = lambda x: False,
                  arg: Any = None):
        time.loop(untiltime=untiltime, timeout=timeout,
                  condition=condition, conditionarg=arg,
                  eachloop=self.each_loop, timeeachlooparg=True, eachloopreturn=False)

    def animate(self, **kwargs) -> anm.ArtistAnimation:
        plot.artistanimate_daemon(self, **kwargs)


class CentralDaemon:
    pass


class UnfairDaemon:
    pass


DaemonType = NewType(
    'DaemonType', Union[FairDaemon, CentralDaemon, UnfairDaemon])


class ManetDaemon(FairDaemon):
    def __init__(self, f: field.Field):
        super().__init__(f.graph)
        self.field = f

    def each_loop(self, t):
        self.field.update(t)
        return super().each_loop(t)

    def animate(self, **kwargs) -> anm.ArtistAnimation:
        plot.artistanimate_manet_daemon(self, **kwargs)
