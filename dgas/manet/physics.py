from __future__ import annotations
from typing import Union, Iterable, Tuple

import torch

from dgas import rc


def distance(pos: torch.Tensor) -> torch.Tensor:
    """
    get the distance of all pairs. O(n^2) in torch.

    Arguments:
        pos {torch.Tensor} -- position array (n*2)

    Returns:
        torch.Tensor -- distance mat (n*n*2)
    """
    return torch.norm(pos[None, :, :] - pos[:, None, :], dim=-1)


def gravity(pos: torch.Tensor, coefficient=1.0, power=2) -> torch.Tensor:
    """
    get the gravity of all pairs. O(n^2) in torch.

    Arguments:
        pos {torch.Tensor} -- position array (n*2)

    Keyword Arguments:
        coefficient {float} -- coefficient of gravity (default: {1.0})
        power {int} -- inversely proportional to the power of the distance (default: {2})

    Returns:
        torch.Tensor -- gravity mat (n*n*2). mat[i, j] is force from j to i.
    """
    vec_ij = pos[None, :, :] - pos[:, None, :]  # vec_ij 's norm is not 1,
    k = coefficient / distance(pos)**(power+1)  # so must +1 to power
    k[k == float('inf')] = 0
    return k[:, :, None] * vec_ij     # gravity[i,j] = force from j to i


def gravity_from_line(pos: torch.Tensor, p1: torch.Tensor, p2: torch.Tensor,
                      coefficient=1.0, power=2) -> torch.Tensor:
    """
    get the gravity from the line connecting p1 and p2.

    Arguments:
        pos {torch.Tensor} -- position array (n*2)
        p1 {torch.Tensor} -- points where the line passes, but not p2.
        p2 {torch.Tensor} -- points where the line passes, but not p1.

    Keyword Arguments:
        coefficient {float} -- coefficient of gravity (default: {1.0})
        power {int} -- inversely proportional to the power of the distance (default: {2})

    Returns:
        torch.Tensor -- gravity mat (n*n*2)
    """
    u = ((p2 - p1) / torch.norm(p2 - p1))[None, :]
    posh = (pos - p1[None, :]) @ u.T * u + p1[None, :] - pos
    k = coefficient / torch.norm(posh, dim=-1)**(power+1)
    return k[:, None] * posh    # posh 's norm is not 1, so must +1 to power


def to_unitvec(vec: torch.Tensor) -> torch.Tensor:
    """
    get the unit vector of given vector. O(n) in torch.

    Arguments:
        vec {torch.Tensor} -- vector (n*1)

    Returns:
        torch.Tensor -- unit vector of length 1.0 (n*1)
    """
    return vec / torch.norm(vec)


def judge_region(pos: torch.Tensor, p1: torch.Tensor, p2: torch.Tensor,
                 basepoint: torch.Tensor = None) -> torch.Tensor:
    """
    judge pos[i] belong to which region where line connecting p1 and p2 are divided.

    Arguments:
        pos {torch.Tensor} -- position array (n*2)
        p1 {torch.Tensor} -- points where the line passes, but not p2.
        p2 {torch.Tensor} -- points where the line passes, but not p1.

    Keyword Arguments:
        basepoint {torch.Tensor} -- basepoint for friendly return. (default: {None})

    Returns:
        torch.Tensor -- vector(n*1)
                        if basepoint == None:
                            the line connecting p1 and p2 rotate left around p1 -> positive
                            the line connecting p1 and p2 rotate right around p1 -> negative
                            on the line connecting p1 and p2 -> 0
                        else:
                            same region to basepoint -> positive
                            opposite region to basepoint -> negative
                            on the line connecting p1 and p2 -> 0
    """
    if basepoint == None:
        u, p = pos - p1, p2 - p1
        # return torch.cross(p, u)
        return u[:, 1] * p[0] - u[:, 0] * p[1]
    else:
        u, p, b = pos - p1, p2 - p1, basepoint - p1
        cross = u[:, 1] * p[0] - u[:, 0] * p[1]
        basecross = (p[0] * b[1] - p[1] * b[0]).item()
        if basecross > 0:
            return cross
        elif basecross < 0:
            return -cross
        else:
            raise ValueError('basepoint is on the line connecting p1 and p2')


def rotation2d(p: torch.Tensor, rad: float, o: torch.Tensor = None):
    if o == None:
        o = torch.tensor([0, 0], dtype=torch.float, device=rc.device)
    if not isinstance(rad, torch.Tensor):
        rad = torch.tensor([rad], dtype=torch.float, device=rc.device)
    op = p - o
    rotmat = torch.tensor([[torch.cos(rad), -torch.sin(rad)],
                           [torch.sin(rad), torch.cos(rad)]],
                          dtype=torch.float, device=rc.device)
    return rotmat @ op + o
