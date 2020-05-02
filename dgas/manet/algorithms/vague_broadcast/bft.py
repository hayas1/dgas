from __future__ import annotations
from typing import Tuple, Type, Dict

import networkx as nx

from dgas import rc, node, graph
from dgas.manet.algorithms.vague_broadcast import simulator


class BftField(simulator.BroadcastLoggingField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        for parent, child in self.breadth_first_tree().edges():
            parent.oracle_sendable.add(child.identifier)
            if rc.bft_edge_color:
                edge = self.graph.edges[parent, child][rc.edge_key]
                edge.drawable().color = rc.bft_edge_color
                edge.drawable().width = rc.colored_edge_width

    def breadth_first_tree(self) -> nx.DiGraph:
        return nx.bfs_tree(self.graph, self.rootnode)


class BftNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)

    ### test ###
    # def oracle_broadcast(self, msg):
    #     to = set(self.neighbors()) & self.oracle_sendable
    #     print(self.identifier, to)
    #     return super().oracle_broadcast(msg)


class BftSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_bft, n, xlen, ylen,
                         node_class=BftNode, field_class=BftField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
