from __future__ import annotations
from typing import Union, List, Set

import torch

from dgas import rc, graph, node, message, plot


class EdgeData:
    def __init__(self, weight=None, drawable: plot.DrawableEdge = None):
        self.drawable_stack = [drawable or plot.DrawableEdge()]
        self.weight = weight or rc.edge_weight

    def drawable(self) -> plot.DrawableEdge:
        return self.drawable_stack[-1]
