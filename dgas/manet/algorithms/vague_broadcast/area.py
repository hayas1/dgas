from __future__ import annotations
from typing import Tuple, Type, Dict, List
import math

import networkx as nx
import torch

from dgas import rc, node, graph
from dgas.manet import physics
from dgas.manet.algorithms.vague_broadcast import simulator


class AreaField(simulator.BroadcastLoggingField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        dist = physics.distance(self.colliders.pos)
        attr = nx.get_node_attributes(self.graph, rc.collider_index_key)
        root_index = attr[self.rootnode]
        for node in self.nodes:
            if node.is_root():
                node.oracle_sendable.update(
                    [n.identifier for n in self.nodes if not n.is_root()])
            else:
                node.oracle_sendable.update(
                    self.same_area(node, attr[node], root_index))

    def same_area(self, n: node.Node, index: int, root_index: int) -> List[node.Node]:
        pos = self.colliders.pos
        rotated = physics.rotation2d(pos[root_index], math.pi/2, pos[index])
        area = physics.judge_region(self.colliders.pos, rotated, pos[index],
                                    basepoint=pos[root_index])
        opposite = torch.where(area < 0)
        return [self.nodes[i].identifier for i in opposite[0]]


class AreaNode(simulator.BroadcastNode):
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


class AreaSimulator(simulator.BroadcastSimulator):
    def __init__(self, n: int, xlen: rc.Number, ylen: rc.Number,
                 untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None, conditionend=False,
                 identifierdraw=False, edgedraw=True, messagedraw=False, **kwargs):
        super().__init__(rc.algname_area, n, xlen, ylen,
                         node_class=AreaNode, field_class=AreaField,
                         untiltime=untiltime, timeout=timeout, conditionend=conditionend,
                         identifierdraw=identifierdraw, edgedraw=edgedraw,
                         messagedraw=messagedraw, **kwargs)
