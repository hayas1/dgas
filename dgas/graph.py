from __future__ import annotations
from typing import Union, Tuple, Iterable, Type, Dict, List, Set, NewType, Sequence

import networkx as nx

from dgas import rc, node, edge, message, result


def make_graph(graphtype: Union[str, nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph] = nx.Graph,
               messages: Dict[node.Node, Set[message.Message]] = None) -> GraphType:
    if (graphtype == rc.undirected_graph) or (graphtype == nx.Graph):
        return UndirectedGraph(messages)
    elif (graphtype == rc.directed_graph) or (graphtype == nx.DiGraph):
        return DirectedGraph(messages)
    elif (graphtype == rc.undirected_multigraph) or (graphtype == nx.MultiGraph):
        return UndirectedMultiGraph(messages)
    elif (graphtype == rc.directed_multigraph) or (graphtype == nx.MultiDiGraph):
        return DirectedMultiGraph(messages)
    else:
        raise ValueError(f'unresolved graph type {graphtype}.')


class GraphWithMessage():
    def __init__(self, messages: Dict[node.Node, Set[message.Message]] = None):
        self.sendings = messages or {}

    def messages(self) -> List[message.Message]:
        return [msg for msgs in self.sendings.values() for msg in msgs]

    def get_sending(self, from_node: node.Node) -> Set[message.Message]:
        return self.sendings.get(from_node, set())

    def add_message(self, from_node: node.Node, msg: message.Message):
        self.sendings[from_node] = self.sendings.get(from_node, set()) | {msg}

    def extend_messages(self, from_node: node.Node, msgs: Iterable[message.Message]):
        self.sendings[from_node] = self.sendings.get(
            from_node, set()) | {*msgs}

    def remove_message(self, from_node: node.Node, msg: message.Message):
        node_sending = self.sendings.get(from_node)
        if node_sending:
            node_sending -= {msg}
        if not node_sending:
            self.sendings.pop(from_node, None)

    def remove_messages_from_node(self, from_node: node.Node, msgs: Iterable[message.Message]):
        node_sending = self.sendings.get(from_node)
        if node_sending:
            node_sending -= {*msgs}
        if not node_sending:
            self.sendings.pop(from_node, None)


class UndirectedGraph(GraphWithMessage, nx.Graph):
    def __init__(self, messages: Dict[node.Node, Set[message.Message]] = None):
        GraphWithMessage.__init__(self, messages)
        nx.Graph.__init__(self)


class DirectedGraph(GraphWithMessage, nx.DiGraph):
    def __init__(self, messages: Dict[node.Node, Set[message.Message]] = None):
        GraphWithMessage.__init__(self, messages)
        nx.DiGraph.__init__(self)


class UndirectedMultiGraph(GraphWithMessage, nx.MultiGraph):
    def __init__(self, messages: Dict[node.Node, Set[message.Message]] = None):
        GraphWithMessage.__init__(self, messages)
        nx.MultiGraph.__init__(self)


class DirectedMultiGraph(GraphWithMessage, nx.MultiDiGraph):
    def __init__(self, messages: Dict[node.Node, Set[message.Message]] = None):
        GraphWithMessage.__init__(self, messages)
        nx.MultiDiGraph.__init__(self)


GraphType = NewType('GraphType', Union[UndirectedGraph,
                                       DirectedGraph, UndirectedMultiGraph, DirectedMultiGraph])
