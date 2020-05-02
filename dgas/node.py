from __future__ import annotations
from typing import Union, List, Dict, Set, Iterable, Callable

import torch

from dgas import rc, graph, edge, message, plot, result


class Node:
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        self._graph = g
        self.drawable_stack = [drawable or plot.DrawableNode()]
        self.identifier = identifier
        self.clashed = False

    def drawable(self) -> plot.DrawableNode:
        return self.drawable_stack[-1]

    def __str__(self) -> str:
        return f'{{node: {{id: {self.identifier}, clashed: {self.clashed}}}}}'

    def neighbors_id(self) -> Dict[rc.NodeID, Node]:
        '''
        dictionary whose key is node's ID and value is node's instance.
        if node's ID is None, for example anonymous network, this method return size 1 dict.
        this method is O(self.degree()) so should save returned dict instance.
        '''
        return {nei.identifier: nei for nei in self._graph.neighbors(self)}

    def neighbors(self) -> List[rc.NodeID]:
        '''
        get this node's neighbors.
        probably O(self.degree()) according to networkx src.
        '''
        return [nei.identifier for nei in self._graph.neighbors(self)]

    def degree(self) -> int:
        '''
        get this node's degree.
        probably O(1) according to networkx src.
        '''
        return self._graph.degree[self]

    def sending(self) -> Set[message.Message]:
        return self._graph.get_sending(self)

    def inject(self, to_node: Node, msg: rc.MessageType, drawable: plot.DrawableMessage = None):
        '''
        O(1), of course. if this node is clashed, cannot inject message.
        TODO? copy msg
        '''
        if not self.clashed:
            e: edge.EdgeData = self._graph[self][to_node][rc.edge_key]
            self._graph.add_message(self, message.Message(
                msg, self, to_node, e, drawable))
            self.on_inject(to_node, msg)

    def receive(self, from_node: Node, msg: rc.MessageType):
        if not self.clashed:
            self.on_receive(msg)

    def send(self, to: rc.NodeID, msg: rc.MessageType, drawable: plot.DrawableMessage = None):
        '''
        O(self.degree()) because find Node instance by it's ID from neighbors.
        '''
        self.inject(self.neighbors_id()[to], msg, drawable)

    def flooding(self, msg: rc.MessageType, drawable: plot.DrawableMessage = None):
        '''
        O(self.degree()), of course.
        '''
        for nei in self._graph.neighbors(self):
            self.inject(nei, msg, drawable)

    def broadcast(self, msg: rc.MessageType, drawable: plot.DrawableMessage = None,
                  without: Iterable[rc.NodeID] = None):
        '''
        O(self.degree()), and if `without` include non-neighbor, it is ignored.
        '''
        for nei in self._graph.neighbors(self):
            if nei.identifier not in set(without or []):
                self.inject(nei, msg, drawable)

    def broadcast_to(self, msg: Union[rc.MessageType, Callable[[rc.NodeID], rc.MessageType]],
                     to: Iterable[rc.NodeID],
                     drawable: Union[plot.DrawableMessage, Iterable[plot.DrawableMessage]] = None):
        '''
        O(self.degree()) because find Node instance by it's ID from neighbors.
        '''
        nei_dict = self.neighbors_id()
        if callable(msg):
            for nei_id, d in zip(to, drawable):
                self.inject(nei_dict[nei_id], msg(nei_id), d)
        else:
            for nei_id in to:
                self.inject(nei_dict[nei_id], msg, drawable)

    def clash(self):
        if not self.clashed:
            self.clashed = True
            self.drawable_stack.append(
                plot.DrawableNode(color=rc.node_clashed_color))
            self.on_crash()

    def recover(self):
        if self.clashed:
            self.clashed = False
            self.drawable_stack.pop()
            self.on_recover()

    def on_inject(self, to_node: Node, msg: rc.MessageType):
        '''
        this method is called when inject message.
        '''

    def on_receive(self, msg: rc.MessageType):
        '''
        this method is called when receive message.
        but if this node is clashed, this method is never called.
        '''

    def on_crash(self):
        '''
        this method is called when crash this node.
        '''

    def on_recover(self):
        '''
        this method is called when recover this node.
        '''

    def update(self, t: rc.GlobalTime):
        '''
        this method is called each frame.
        '''
        pass


class LoggingNode(Node):
    def __init__(self, g: Union[graph.UndirectedGraph, graph.DirectedGraph,
                                graph.UndirectedMultiGraph, graph.DirectedMultiGraph],
                 identifier: rc.NodeID = None, drawable: plot.DrawableNode = None):
        super().__init__(g, identifier=identifier, drawable=drawable)
        self.record = result.NodeRecord(identifier)

    def inject(self, to_node: Node, msg: rc.MessageType, drawable: plot.DrawableMessage = None):
        self.record.sended_message.append(
            result.MessageRecord(self.record.frame, to_node, msg))
        return super().inject(to_node, msg, drawable=drawable)

    def receive(self, from_node: Node, msg: rc.MessageType):
        self.record.received_message.append(
            result.MessageRecord(self.record.frame, from_node, msg))
        return super().receive(from_node, msg)

    def update(self, t):
        self.record.frame = t
        return super().update(t)
