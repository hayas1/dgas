import argparse
import os
import sys
import datetime as dt
from multiprocessing import Pool

from tqdm import tqdm
import matplotlib.pyplot as plt

from dgas import rc
from dgas.manet.algorithms.vague_broadcast import flooding, bft, mst, bftmst, hop, gthop, far, area

FLOODING = rc.algname_flooding
FAR = rc.algname_far
AREA = rc.algname_area
HOP = rc.algname_hop
GTHOP = rc.algname_gthop
BFT = rc.algname_bft
MST = rc.algname_mst
BFTMST = rc.algname_bftmst


def arg_parser():
    parser = argparse.ArgumentParser(
        description='simulate vague broadcast of mobile network concurrently.')
    parser.add_argument('algorithms', choices=[FLOODING, FAR, AREA, HOP, GTHOP, BFT, MST, BFTMST],
                        nargs='*', help='kind of vague broadcast algorithm')
    parser.add_argument('-n', '--nodes', metavar='n', type=int,
                        help='set the number of node (if set this, rangelist is ignored)')
    parser.add_argument('-r', '--rangelist', nargs='*', metavar='nodes',
                        default=[50, 100, 150, 200, 250, 300], type=int,
                        help='list of the number of node (if set nodes, this arg is ignored)')
    parser.add_argument('-t', '--times', type=int, nargs='*', metavar='times', default=[100],
                        help='simulation times on the same number of nodes (length is 1 or same to rangelist)')
    # parser.add_argument('-c', '--concurrent', type=int, metavar='processes',
    #                     help='use multi processing (*developping...)')
    parser.add_argument('-a', '--animate',
                        action='store_true', help='output animation')
    parser.add_argument('-s', '--size', nargs=2, metavar=('x', 'y'), default=[rc.field_xlen, rc.field_ylen],
                        type=float, help='field size (x, y)')
    parser.add_argument('-f', '--frames', metavar='frames',
                        type=int, help='set frame of simulation')
    parser.add_argument('-l', '--limits', metavar='timeout',
                        type=int, help='timeout frame of simulation')
    parser.add_argument('-o', '--out', metavar='path', default=r'.\out',
                        help='output path of result (and animation)')
    parser.add_argument('-d', '--delay', type=int, metavar='d',
                        default=rc.node_delay, help='the delay of message transition')
    return parser


def range_generator(nodes, rangelist, times):
    if nodes:
        if len(times) == 1:
            return (nodes for _ in range(times[0]))
        else:
            raise ValueError('if set nodes, times length must be 1.')
    else:
        if len(times) == 1:
            return (n for n in rangelist for _ in range(times[0]))
        elif len(times) == len(rangelist):
            return (n for n in rangelist for _ in times)
        else:
            raise ValueError(
                'if set nodes, times length must be same to rangelist.'
                + f'len(times): {len(times)}, len(rangelist): {len(rangelist)}')


def simulator_class(algorithm):
    if algorithm == rc.algname_flooding:
        return flooding.FloodingSimulator
    elif algorithm == rc.algname_bft:
        return bft.BftSimulator
    elif algorithm == rc.algname_mst:
        return mst.MstSimulator
    elif algorithm == rc.algname_bftmst:
        return bftmst.BftMstSimulator
    elif algorithm == rc.algname_hop:
        return hop.HopSimulator
    elif algorithm == rc.algname_gthop:
        return gthop.GthopSimulator
    elif algorithm == rc.algname_far:
        return far.FarSimulator
    elif algorithm == rc.algname_area:
        return area.AreaSimulator
    else:
        raise ValueError(f'unexpected algorithm {algorithm}.')


def simulator_generator(algorithm, frames, limits, field_xy, rangelist):
    sc = simulator_class(algorithm)
    return (sc(n, *field_xy, untiltime=frames, timeout=limits,
               conditionend=(frames == None) and (limits == None)) for n in rangelist)


def make_workspace(out, delay, algorithm):
    workspace = os.path.join(out, f'delay{delay}', algorithm)
    os.makedirs(workspace, exist_ok=True)
    return workspace


def print_start(algorithm, nodes, nodeslist, times):
    print(
        f'start {algorithm} simulation {nodes or nodeslist} nodes in {times} times...')


def print_end(algorithm, rangelist, outdir):
    print(f'finish {algorithm} simulation in {len(rangelist)} times.'
          + f' saved {len(outdir)} directories.')


def simulation(algorithm, nodes, nodeslist, times, delay, out, field_xy,
               animate, printprogress=True):
    rc.node_delay = delay
    rc.bft_edge_color = rc.mst_edge_color = rc.bftmst_edge_color = None
    rangelist = list(range_generator(nodes, nodeslist, times))
    workspace = make_workspace(out, delay, algorithm)
    simulators = simulator_generator(algorithm, frames, limits,
                                     field_xy, rangelist)
    results = []
    if printprogress:
        print_start(algorithm, nodes, nodeslist, times)
    for simulator in tqdm(simulators, total=len(rangelist)):
        outdir = simulator.run_and_save(workspace, ani=animate,
                                        mkdir=True, connectedonly=True)
        if outdir:
            results.append(outdir)
        if animate:
            plt.close()
    if printprogress:
        print_end(algorithm, rangelist, results)


if __name__ == '__main__':
    args = arg_parser().parse_args()
    algorithms, nodes, nodeslist = args.algorithms, args.nodes, args.rangelist
    times, animate, field_xy = args.times, args.animate, args.size
    frames, limits, out, delay = args.frames, args.limits, args.out, args.delay
    for alg in algorithms:
        simulation(alg, nodes, nodeslist, times, delay, out, field_xy,
                   animate, printprogress=True)
