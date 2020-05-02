from __future__ import annotations
from typing import Tuple, Type, Dict

import networkx as nx

from dgas import rc, node, graph
from dgas.manet.algorithms.vague_broadcast import simulator, hop


class GthopField(hop.HopField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)

    def is_far(self, d: Dict[node.Node, int], u: node.Node, v: node.Node) -> bool:
        return d.get(u, float('inf')) < d.get(v, float('inf'))


class GthopNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)

    ### test ###
    # def oracle_broadcast(self, msg):
    #     to = set(self.neighbors()) & self.oracle_sendable
    #     print(self.identifier, to)
    #     return super().oracle_broadcast(msg)


class GthopSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_gthop, n, xlen, ylen,
                         node_class=GthopNode, field_class=GthopField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
