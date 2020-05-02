from __future__ import annotations
from typing import Tuple, Type, Dict

import torch

from dgas import rc, node, edge, message, graph, result, daemon, plot
from dgas.manet import physics


def antigravity(n: int, coefficient=0.05) -> np.array:
    pos = torch.rand(n, 2, device=rc.device)*10
    vel = torch.zeros(n, 2, device=rc.device)
    acc = torch.zeros(n, 2, device=rc.device)
    for _ in range(10):
        acc -= torch.sum(physics.gravity(pos, coefficient=coefficient), dim=1)
        vel += acc
        pos += vel
        pos = torch.where(0 < pos, pos, torch.ones_like(pos)*10+pos)
        pos = torch.where(pos < torch.ones_like(pos)*10,
                          pos, torch.zeros_like(pos)+pos-10)
    pos = torch.clamp(pos, 0, 10)
    return pos
