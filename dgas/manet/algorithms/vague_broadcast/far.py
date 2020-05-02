from __future__ import annotations
from typing import Tuple, Type, Dict

import networkx as nx
import torch

from dgas import rc, node, graph
from dgas.manet import physics
from dgas.manet.algorithms.vague_broadcast import simulator


class FarField(simulator.BroadcastLoggingField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        dist = physics.distance(colliders.pos)
        attr = nx.get_node_attributes(self.graph, rc.collider_index_key)
        root_index = attr[self.rootnode]
        for node in self.nodes:     # we can use enumerate()
            for other in self.nodes:
                u, v = attr[node], attr[other]
                if node != other and self.is_far(dist, root_index, u, v):
                    node.oracle_sendable.add(other.identifier)

    def is_far(self, dist: torch.Tensor, r: int, u: int, v: int) -> bool:
        return dist[r, u] < dist[r, v]


class FarNode(simulator.BroadcastNode):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)

    ### test ###
    # def oracle_broadcast(self, msg):
    #     # to = set(self.neighbors()) & self.oracle_sendable
    #     to = self.oracle_sendable
    #     print(self.identifier, to)
    #     return super().oracle_broadcast(msg)


class FarSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_far, n, xlen, ylen,
                         node_class=FarNode, field_class=FarField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
