from __future__ import annotations
from typing import Tuple, Type, Dict

import torch
import numpy as np
from scipy.sparse import csgraph, csr_matrix
import networkx as nx

from dgas import rc, node, edge, message, graph, result
from dgas.manet import collider, physics


def init_random(n: int, xlen: rc.Number, ylen: rc.Number,
                node_class: Type[node.Node] = None,
                field_class: Type[Field] = None, identifier=True):
    g = graph.make_graph(rc.undirected_graph)
    nodes, pos, vel = [], [], []
    for i in range(n):
        # TODO 初期状況で連結でない場合
        node = (node_class or node.Node)(g, i if identifier else None)
        pos.append((torch.rand(2) * torch.tensor([xlen, ylen])).tolist())
        vel.append((rc.rand_node_vel_min + (rc.rand_node_vel_max -
                                            rc.rand_node_vel_min) * torch.rand(2)).tolist())
        nodes.append(node)
    g.add_nodes_from((node, {rc.collider_index_key: i})
                     for i, node in enumerate(nodes))
    colliders = collider.NodeColliderList(
        rc.manet_node_size, rc.communication_radius, pos, vel)
    return (field_class or GravityField)(g, colliders, xlen, ylen, origin=(0, 0), nodelist=nodes)


class Field:
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        # default origin (0, 0) is self.southwest
        self.graph = g
        self.nodes = nodelist or list(g.nodes())    # read only field
        self.colliders = colliders      # read only field
        self.xlen = xlen
        self.ylen = ylen
        self.origin = torch.tensor(origin, dtype=torch.float, device=rc.device)
        self.connectivity = True

    @property
    def north(self) -> rc.Number:
        return self.ylen - self.origin[1].item()

    @property
    def south(self) -> rc.Number:
        return 0 - self.origin[1].item()

    @property
    def west(self) -> rc.Number:
        return 0 - self.origin[0].item()

    @property
    def east(self) -> rc.Number:
        return self.xlen - self.origin[0].item()

    @property
    def northwest(self) -> torch.Tensor:
        return torch.tensor([self.west, self.north], dtype=torch.float, device=rc.device)

    @property
    def southeast(self) -> torch.Tensor:
        return torch.tensor([self.east, self.south], dtype=torch.float, device=rc.device)

    @property
    def northeast(self) -> torch.Tensor:
        return torch.tensor([self.east, self.north], dtype=torch.float, device=rc.device)

    @property
    def southwest(self) -> torch.Tensor:
        return torch.tensor([self.west, self.south], dtype=torch.float, device=rc.device)

    def north_projection(self, points: torch.Tensor) -> torch.Tensor:
        return points * torch.tensor([1, 0], dtype=torch.float, device=rc.device)\
            + torch.tensor([0, self.north],
                           dtype=torch.float, device=rc.device)

    def south_projection(self, points: torch.Tensor) -> torch.Tensor:
        return points * torch.tensor([1, 0], dtype=torch.float, device=rc.device)\
            + torch.tensor([0, self.south],
                           dtype=torch.float, device=rc.device)

    def west_projection(self, points: torch.Tensor) -> torch.Tensor:
        return points * torch.tensor([0, 1], dtype=torch.float, device=rc.device)\
            + torch.tensor([self.west, 0],
                           dtype=torch.float, device=rc.device)

    def east_projection(self, points: torch.Tensor) -> torch.Tensor:
        return points * torch.tensor([0, 1], dtype=torch.float, device=rc.device)\
            + torch.tensor([self.east, 0],
                           dtype=torch.float, device=rc.device)

    def north_extract(self, vec: torch.Tensor) -> torch.Tensor:
        return vec * torch.tensor([0, 1], dtype=torch.float, device=rc.device)

    def south_extract(self, vec: torch.Tensor) -> torch.Tensor:
        return vec * torch.tensor([0, -1], dtype=torch.float, device=rc.device)

    def west_extract(self, vec: torch.Tensor) -> torch.Tensor:
        return vec * torch.tensor([-1, 0], dtype=torch.float, device=rc.device)

    def east_extract(self, vec: torch.Tensor) -> torch.Tensor:
        return vec * torch.tensor([1, 0], dtype=torch.float, device=rc.device)

    def pos_dict(self) -> Dict[node.Node, np.ndarray]:
        return {n: self.colliders.pos[i].cpu().numpy() for n, i in self.graph.nodes(rc.collider_index_key)}

    def node_index(self) -> Dict[node.Node, int]:
        return {n: i for n, i in self.graph.nodes(rc.collider_index_key)}

    def force_in_field(self, refrect=True) -> Tuple[torch.Tensor, torch.Tensor]:
        size, pos, vel = self.colliders.size, self.colliders.pos, self.colliders.vel
        center = (self.southwest + self.northeast) / 2
        north_out = (pos + self.north_extract(size))[:, 1] > self.north
        south_out = (pos + self.south_extract(size))[:, 1] < self.south
        west_out = (pos + self.west_extract(size))[:, 0] < self.west
        east_out = (pos + self.east_extract(size))[:, 0] > self.east
        if refrect:
            rev_x = torch.tensor([-1, 1], dtype=torch.float, device=rc.device)
            rev_y = torch.tensor([1, -1], dtype=torch.float, device=rc.device)
            vel[north_out] = rev_y * vel[north_out]
            vel[south_out] = rev_y * vel[south_out]
            vel[west_out] = rev_x * vel[west_out]
            vel[east_out] = rev_x * vel[east_out]
        pos[north_out] = (self.north_projection(pos)
                          - self.north_extract(size))[north_out]
        pos[south_out] = (self.south_projection(pos)
                          - self.south_extract(size))[south_out]
        pos[west_out] = (self.west_projection(pos)
                         - self.west_extract(size))[west_out]
        pos[east_out] = (self.east_projection(pos)
                         - self.east_extract(size))[east_out]
        return pos, vel

    def clamp_velocity(self, min=None, max=None):
        abs_vel = torch.norm(self.colliders.vel, dim=-1)
        clamped = torch.clamp(abs_vel, min or 0, max or float('inf'))
        return (clamped / abs_vel)[:, None] * self.colliders.vel

    def update(self, t: rc.GlobalTime):
        self.update_colliders(t)
        self.connectivity = nx.is_connected(self.graph)

    def update_colliders(self, t: rc.GlobalTime):
        self.colliders.pos, self.colliders.vel = self.force_in_field(
            rc.wall_reflection)
        self.colliders.vel = self.clamp_velocity(
            rc.min_abs_vel, rc.max_abs_vel)


class GravityField(Field):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        self.edges = torch.zeros((len(self.nodes), len(self.nodes)),
                                 dtype=torch.float, device=rc.device)
        self.removed_edges = None
        self.added_edges = None
        self.update_edge(-1)    # make networkx edge

    def wall_repultion(self, coefficient=1.0, power=2) -> torch.Tensor:
        pos = self.colliders.pos
        north = -physics.gravity_from_line(pos, self.northwest, self.northeast,
                                           coefficient, power)
        south = -physics.gravity_from_line(pos, self.southwest, self.southeast,
                                           coefficient, power)
        west = -physics.gravity_from_line(pos, self.northwest, self.southwest,
                                          coefficient, power)
        east = -physics.gravity_from_line(pos, self.northeast, self.southeast,
                                          coefficient, power)
        return north + south + west + east

    def update(self, t: rc.GlobalTime):
        self.update_edge(t)
        super().update(t)

    def update_colliders(self, t: rc.GlobalTime):
        self.colliders.vel += self.wall_repultion(rc.wall_repultion_coefficient,
                                                  rc.wall_repultion_power)
        super().update_colliders(t)
        self.colliders.update(t)

    def update_edge(self, t: rc.GlobalTime):
        prev, new = self.edges, self.colliders.adjacency_matrix()
        self.edges, diff = new, new - prev
        self.removed_edges = [(self.nodes[u], self.nodes[v]) for u, v
                              in zip(*torch.where(diff < 0)) if u != v]
        self.graph.remove_edges_from(self.removed_edges)
        self.added_edges = [(self.nodes[u], self.nodes[v], {rc.edge_key: edge.EdgeData(
            rc.edge_weight)}) for u, v in zip(*torch.where(diff > 0)) if u != v]
        self.graph.add_edges_from(self.added_edges)


class LoggingGravityField(GravityField):
    def __init__(self, g: graph.GraphType, colliders: collider.NodeColliderList,
                 xlen: rc.Number, ylen: rc.Number, origin=(0, 0), nodelist=None):
        super().__init__(g, colliders, xlen, ylen, origin=origin, nodelist=nodelist)
        self.record = result.FieldRecord()

    def update(self, t: rc.GlobalTime):
        self.record.pos.append(self.colliders.pos.tolist())
        self.record.connectivity.append(self.connectivity)
        super().update(t)

    def update_edge(self, t: rc.GlobalTime):
        if t == 0:
            self.record.first_edges = len(self.added_edges)
        super().update_edge(t)
        if t >= 0:
            self.record.added_edges += len(self.added_edges)
            self.record.removed_edges += len(self.removed_edges)
