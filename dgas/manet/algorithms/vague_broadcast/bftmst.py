from __future__ import annotations
from typing import Tuple, Type, Dict

import networkx as nx

from dgas import rc, node, graph
from dgas.manet.algorithms.vague_broadcast import simulator, bft, mst


class BftMstField(bft.BftField, mst.MstField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        bft_color, mst_color = rc.bft_edge_color, rc.mst_edge_color
        rc.bft_edge_color = rc.mst_edge_color = None
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        rc.bft_edge_color, rc.mst_edge_color = bft_color, mst_color
        indic = {node.identifier: node for node in self.nodes}
        for node in self.nodes:
            for child_id in node.oracle_sendable:
                if rc.bftmst_edge_color:
                    edge = self.graph.edges[node, indic[child_id]][rc.edge_key]
                    edge.drawable().color = rc.bftmst_edge_color
                    edge.drawable().width = rc.colored_edge_width


class BftMstNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)

    ### test ###
    # def oracle_broadcast(self, msg):
    #     to = set(self.neighbors()) & self.oracle_sendable
    #     print(self.identifier, to)
    #     return super().oracle_broadcast(msg)


class BftMstSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_bftmst, n, xlen, ylen,
                         node_class=BftMstNode, field_class=BftMstField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
