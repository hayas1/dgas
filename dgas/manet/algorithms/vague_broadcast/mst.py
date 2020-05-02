from __future__ import annotations
from typing import Tuple, Type, Dict

import networkx as nx

from dgas import rc, node, graph
from dgas.manet.algorithms.vague_broadcast import simulator


class MstField(simulator.BroadcastLoggingField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        mst = self.minimum_spanning_tree()
        mst_children = dict(nx.bfs_successors(mst, self.rootnode))
        for node in self.nodes:
            for child in mst_children.get(node, []):
                node.oracle_sendable.add(child.identifier)
                if rc.mst_edge_color:
                    edge = self.graph.edges[node, child][rc.edge_key]
                    edge.drawable().color = rc.mst_edge_color
                    edge.drawable().width = rc.colored_edge_width

    def minimum_spanning_tree(self) -> nx.Graph:
        g = nx.Graph()
        g.add_nodes_from(self.nodes)
        g.add_edges_from((self.nodes[u], self.nodes[v], {'weight': w}) for u, v, w
                         in self.colliders.edge_list(distweight=True))
        return nx.minimum_spanning_tree(g, weight='weight')


class MstNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)

    ### test ###
    # def oracle_broadcast(self, msg):
    #     to = set(self.neighbors()) & self.oracle_sendable
    #     print(self.identifier, to)
    #     return super().oracle_broadcast(msg)


class MstSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_mst, n, xlen, ylen,
                         node_class=MstNode, field_class=MstField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
