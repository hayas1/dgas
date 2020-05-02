from __future__ import annotations
from typing import Union, List, Set, Dict

import torch

from dgas import rc, node, edge, plot


def position(message: Message, pos: Dict[node.Node, torch.Tensor]) -> torch.Tensor:
    frompos, topos = pos[message.from_node], pos[message.to_node]
    return frompos + (topos - frompos) * message.progress()


class Message:
    def __init__(self, msg: rc.MessageType, from_node: node.Node, to_node: node.Node,
                 edgedata: edge.EdgeData, drawable: plot.DrawableMessage = None):
        self.drawable_stack = [drawable or plot.DrawableMessage()]
        self.raw: rc.MessageType = msg.raw if isinstance(msg, Message) else msg
        self.from_node = from_node
        self.to_node = to_node
        self.edge = edgedata
        self.init_life = edgedata.weight
        self.remain_life = edgedata.weight

    def drawable(self) -> plot.DrawableMessage:
        return self.drawable_stack[-1]

    def arrive(self) -> bool:
        return self.remain_life <= 0

    def progress(self) -> float:
        return 1 - self.remain_life / self.init_life

    def update(self, t: rc.GlobalTime):
        self.remain_life -= 1 if self.remain_life > 0 else 0
