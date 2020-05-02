from __future__ import annotations
from typing import Tuple, Type, Dict

import networkx as nx

from dgas import rc, node, graph
from dgas.manet.algorithms.vague_broadcast import simulator


class HopField(simulator.BroadcastLoggingField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        hop = self.shotest_path_hop()
        for node in self.nodes:
            for other in self.nodes:
                if node != other and self.is_far(hop, node, other):
                    node.oracle_sendable.add(other.identifier)

    def is_far(self, d: Dict[node.Node, int], u: node.Node, v: node.Node) -> bool:
        return d.get(u, float('inf')) <= d.get(v, float('inf'))

    def shotest_path_hop(self) -> Dict:
        return nx.shortest_path_length(self.graph, source=self.rootnode)


class HopNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)

    ### test ###
    # def oracle_broadcast(self, msg):
    #     to = set(self.neighbors()) & self.oracle_sendable
    #     print(self.identifier, to)
    #     return super().oracle_broadcast(msg)


class HopSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_hop, n, xlen, ylen,
                         node_class=HopNode, field_class=HopField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
