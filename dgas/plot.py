from __future__ import annotations
from typing import NewType, List, Iterable, Sequence, Tuple, Dict, Union, Callable, Any

import itertools

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as anm
import torch
import networkx as nx
from networkx.drawing import nx_pylab
from collections import abc

from dgas import rc, time, daemon, graph, node, message


class DrawableNode:
    def __init__(self, size=None, color=None,  # shape=None,
                 alpha=None, edgewidth=None, edgecolor=None):
        self.size = size or rc.node_size
        self.color = color or rc.node_color
        # self.shape = shape or rc.node_shape
        self.alpha = alpha or rc.node_alpha
        self.edgewidth = edgewidth or rc.node_edge_width
        self.edgecolor = edgecolor or rc.node_edge_color


def list_from_nodes(nodes: Iterable[DrawableNode]) -> Dict[str, List]:
    nodes = list(nodes)
    size = [node.size for node in nodes]
    color = [node.color for node in nodes]
    # shape = [node.shape for node in nodes]
    alpha = [node.alpha for node in nodes]
    edgewidth = [node.edgewidth for node in nodes]
    edgecolor = [node.edgecolor for node in nodes]
    return {'node_size': size, 'node_color': color,  # 'node_shape': shape,
            'alpha': alpha, 'linewidths': edgewidth, 'edgecolors': edgecolor}


class DrawableEdge:
    def __init__(self, width=None, color=None, style=None,  # alpha=None,
                 hasarrow=None, arrowstyle=None, arrowsize=None):
        self.width = width or rc.edge_width
        self.color = color or rc.edge_color
        self.style = style or rc.edge_style
        # self.alpha = alpha or rc.edge_alpha
        self.hasarrow = hasarrow or rc.edge_arrow
        self.arrowstyle = arrowstyle or rc.edge_arrow_style
        self.arrowsize = arrowsize or rc.edge_arrow_size


def list_from_edges(edges: Iterable[DrawableEdge]) -> Dict[str, List]:
    edges = list(edges)
    width = [edge.width for edge in edges]
    color = [edge.color for edge in edges]
    style = [edge.style for edge in edges]
    # alpha = [edge.alpha for edge in edges]
    arrowstyle = [edge.arrowstyle for edge in edges]
    arrowsize = [edge.arrowsize for edge in edges]
    return {'width': width, 'edge_color': color, 'style': style,  # 'alpha': alpha,
            'arrowstyle': arrowstyle, 'arrowsize': arrowsize}


class DrawableMessage:
    def __init__(self, size=None, color=None, shape=None,
                 alpha=None, edgewidth=None, edgecolor=None):
        self.size = size or rc.message_size
        self.color = color or rc.message_color
        self.shape = shape or rc.message_shape
        self.alpha = alpha or rc.message_alpha
        self.edgewidth = edgewidth or rc.message_edge_width
        self.edgecolor = edgecolor or rc.message_edge_color


def list_from_messages(messages: Iterable[message.Message]) -> List[Tuple[List[message.Message], Dict[str, List]]]:
    def to_dict_of_list(messages: List[message.Message]) -> Tuple[List[message.Message], Dict[str, List]]:
        size = [message.drawable().size for message in messages]
        color = [message.drawable().color for message in messages]
        shape = [message.drawable().shape for message in messages]
        alpha = [message.drawable().alpha for message in messages]
        linewidth = [message.drawable().edgewidth for message in messages]
        linecolor = [message.drawable().edgecolor for message in messages]
        return messages, {'message_size': size, 'message_color': color, 'message_shape': shape,
                          'alpha': alpha, 'linewidths': linewidth, 'linecolors': linecolor}
    return [to_dict_of_list(list(msgs)) for _shape, msgs in itertools.groupby(messages, lambda m: m.drawable().shape)]


def draw_nodes(g: graph.GraphType, pos: Dict[node.Node, torch.Tensor] = None,
               nodelist: List[DrawableNode] = None, ax: plt.Axes = None) -> matplotlib.collections.PathCollection:
    drawable = list_from_nodes(node.drawable()
                               for node in nodelist or g.nodes())
    return nx.draw_networkx_nodes(g, pos, nodelist=nodelist, ax=ax, **drawable)


def draw_identifier(g: graph.GraphType, pos: Dict[node.Node, torch.Tensor] = None,
                    ax=None, **kwargs) -> Dict[node.Node, matplotlib.text.Text]:
    labels = {node: node.identifier for node in g.nodes()}
    return nx.draw_networkx_labels(g, pos, labels, ax=ax, **kwargs)


def draw_edges(g: graph.GraphType, pos: Dict[node.Node, torch.Tensor] = None,
               edgelist: List[DrawableEdge] = None, ax: plt.Axes = None) -> Union[matplotlib.collections.LineCollection, List[matplotlib.patches.FancyArrowPatch]]:
    drawable = list_from_edges(
        edge[2].drawable() for edge in edgelist or g.edges.data(rc.edge_key))
    return nx.draw_networkx_edges(g, pos, edgelist=edgelist, ax=ax, **drawable)


def draw_messages(g: graph.GraphType, pos: Dict[node.Node, torch.Tensor],
                  messagelist: List[message.Message] = None, ax: plt.Axes = None) -> List[matplotlib.collections.PathCollection]:
    messages = messagelist or g.messages()
    axes = ax or plt.gca()
    message_collections = []
    for same_shapes, dic in list_from_messages(message for message in messages):
        size, color, alpha = dic['message_size'], dic['message_color'], dic['alpha']
        linewidth, linecolor = dic['linewidths'], dic['linecolors']
        xy = torch.Tensor([message.position(m, pos) for m in same_shapes])
        if isinstance(alpha, abc.Iterable):
            color = nx_pylab.apply_alpha(color, alpha, same_shapes,
                                         cmap=None, vmin=None, vmax=None)
            alpha = None
        plotted_messages = axes.scatter(xy[:, 0], xy[:, 1], s=size, c=color,
                                        marker=same_shapes[0].drawable().shape,
                                        alpha=alpha, linewidths=linewidth, edgecolors=linecolor)
        plotted_messages.set_zorder(rc.message_zorder)
        message_collections.append(plotted_messages)

    axes.tick_params(axis='both', which='both', bottom=False,
                     left=False, labelbottom=False, labelleft=False)
    return message_collections


def draw_graph(g: graph.GraphType, pos: Dict[node.Node, torch.Tensor] = None,
               identifier=True, ax: plt.Axes = None, **kwargs) -> List[plt.Artist]:
    position = nx.spring_layout(g) if pos == None else pos
    axes = ax or plt.gca()
    nodes = draw_nodes(g, position, ax=axes)
    if identifier:
        label_dic = draw_identifier(g, position, ax=axes, **kwargs)
    edges = draw_edges(g, position, ax=axes)
    messages = draw_messages(g, position, ax=axes)
    labels = list(label_dic.values()) if identifier else []
    return [nodes, edges, *messages, *labels]


def artistanimate_daemon(d: daemon.DaemonType,
                         pos: Dict[node.Node, torch.Tensor] = None,
                         identifier=True, ax: plt.Axes = None, fig: plt.Figure = None,
                         untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None,
                         condition: Callable[[Any], bool] = lambda x: False,
                         arg: Any = None, **kwargs) -> anm.ArtistAnimation:
    position = nx.spring_layout(d.g) if pos == None else pos
    axes = ax or plt.gca()

    def update(t: rc.GlobalTime) -> List[plt.Artist]:
        d.each_loop(t)
        return draw_graph(d.graph, pos=position, identifier=identifier, ax=axes, **kwargs)

    artists_list = time.loop(untiltime=untiltime, timeout=timeout,
                             condition=condition, conditionarg=arg,
                             eachloop=update, timeeachlooparg=True, eachloopreturn=True)
    return anm.ArtistAnimation(fig or plt.gcf(), artists_list, **kwargs)


def artistanimate_manet_daemon(md: daemon.ManetDaemon, identifier=False, message=False,
                               edge=True, ax: plt.Axes = None, fig: plt.Figure = None,
                               untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None,
                               condition: Callable[[Any], bool] = lambda x: False,
                               arg: Any = None, **kwargs) -> anm.ArtistAnimation:
    axes = ax or plt.gca()
    # axes.set_xlim(left=md.field.west, right=md.field.east)
    # axes.set_ylim(bottom=md.field.south, top=md.field.north)

    def update(t: rc.GlobalTime) -> List[plt.Artist]:
        md.each_loop(t)
        position = md.field.pos_dict()
        artists = [draw_nodes(md.graph, position, ax=axes)]
        if identifier:
            label_dic = draw_identifier(md.graph, position, ax=axes, **kwargs)
        if edge:
            artists.append(draw_edges(md.graph, position, ax=axes))
        if message:
            artists.extend(draw_messages(md.graph, position, ax=axes))
        labels = list(label_dic.values()) if identifier else []
        return artists + [*labels]

    artists_list = time.loop(untiltime=untiltime, timeout=timeout,
                             condition=condition, conditionarg=arg,
                             eachloop=update, timeeachlooparg=True, eachloopreturn=True)
    return anm.ArtistAnimation(fig or plt.gcf(), artists_list, **kwargs)
