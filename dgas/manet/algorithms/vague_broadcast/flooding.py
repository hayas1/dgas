from __future__ import annotations
from typing import Tuple, Type, Dict


from dgas import rc, node, graph
from dgas.manet.algorithms.vague_broadcast import simulator


class FloodingField(simulator.BroadcastLoggingField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        for node in self.nodes:
            node.oracle_sendable = set(
                n.identifier for n in self.graph.nodes())


class FloodingNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)


class FloodingSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_flooding, n, xlen, ylen,
                         node_class=FloodingNode, field_class=FloodingField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
