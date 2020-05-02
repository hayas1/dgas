from __future__ import annotations
from typing import Union, Iterable, Tuple, List
from collections import abc
import itertools

import torch
from scipy.sparse import csr_matrix

from dgas import rc
from dgas.manet import physics


class NodeColliderList:
    def __init__(self, size: Union[rc.Number, Iterable[rc.Number]], com_rad: Union[rc.Number, Iterable[rc.Number]],
                 pos: Iterable[Tuple[rc.Number, rc.Number]], vel: Iterable[Tuple[rc.Number, rc.Number]]):
        self.size = torch.tensor(list(size), dtype=torch.float, device=rc.device) if isinstance(
            size, abc.Iterable) else float(size)
        self.com_rad = torch.tensor(list(com_rad), dtype=torch.float, device=rc.device) if isinstance(
            com_rad, abc.Iterable) else float(com_rad)
        self.pos = torch.tensor(list([x, y]for x, y in pos),
                                dtype=torch.float, device=rc.device)
        self.vel = torch.tensor(list([vx, vy]for vx, vy in vel),
                                dtype=torch.float, device=rc.device)

    def __len__(self) -> int:
        return len(self.pos)

    def __iter__(self) -> zip:
        return zip(self.size, self.pos, self.vel)

    def __getitem__(self, key) -> Union[NodeColliderList,
                                        Tuple[rc.Number, torch.Tensor, torch.Tensor]]:
        if isinstance(key, slice):
            return NodeColliderList(self.size[key], self.pos[key], self.vel[key])
        else:
            return self.size[key], self.pos[key], self.vel[key]

    def adjacency_matrix(self, distweight=False) -> torch.Tensor:
        dist = physics.distance(self.pos)
        if distweight:
            return torch.where(dist < self.com_rad, dist, torch.zeros_like(dist))
        else:
            return torch.where(dist < self.com_rad, torch.ones_like(dist), torch.zeros_like(dist))

    def adjacency_list(self) -> List[List[int]]:
        edge = torch.stack(torch.where(
            physics.distance(self.pos) < self.com_rad)).T
        return [list(t[1].item() for t in v) for _i, v in itertools.groupby(edge, key=lambda e: e[0])]

    def edge_list(self, distweight=False) -> List[Tuple[int, int]]:
        dist = physics.distance(self.pos)
        edge = torch.stack(torch.where(dist < self.com_rad)).T
        if distweight:
            return [(u, v, dist[u, v]) for u, v in edge.tolist()]
        else:
            return [(u, v) for u, v in edge.tolist()]

    def update(self, t: rc.GlobalTime):
        self.pos += self.vel
        attraction = physics.gravity(self.pos, rc.attraction_coefficient,
                                     rc.attraction_power)
        repultion = -physics.gravity(self.pos, rc.repultion_coefficient,
                                     rc.repultion_power)
        self.vel += torch.sum(attraction, dim=1) + torch.sum(repultion, dim=1)
