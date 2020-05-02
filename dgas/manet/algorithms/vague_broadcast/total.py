from __future__ import annotations
from typing import Tuple, Type, Dict, List, Any
import json
import datetime as dt
import os
import re

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt


from dgas import rc, node, edge, message, graph, result, daemon, plot
from dgas.manet import collider, physics, field


def splitdelay(delay_int: str) -> int:
    delay_int_str = os.path.splitext(delay_int)[0]
    return int(re.compile(r'\d+$').findall(delay_int_str)[-1])


def total_from(dirpath: str, walk=False) -> ConnectedTotal:
    if walk:
        return total_walk(dirpath)
    else:
        delay_dflist = []
        for delay in [d for d in os.listdir(dirpath) if os.path.isdir(os.path.join(dirpath, d))]:
            ddf = delay_dir(os.path.join(dirpath, delay))
            ddf.insert(0, rc.pd_delay, splitdelay(delay))
            delay_dflist.append(ddf)
        return ConnectedTotal(pd.concat(delay_dflist))


def delay_dir(delaydir: str) -> pd.DataFrame:
    delay = splitdelay(os.path.basename(delaydir))
    alg_dflist = []
    for algorithm in [d for d in os.listdir(delaydir) if os.path.isdir(os.path.join(delaydir, d))]:
        adf = algorithm_dir(os.path.join(delaydir, algorithm), delay)
        adf.insert(0, rc.pd_algorithm, algorithm)
        alg_dflist.append(adf)
    return pd.concat(alg_dflist)


def algorithm_dir(algdir: str, delay: rc.GlobalTimeDelta) -> pd.DataFrame:
    to_pd = {rc.pd_nodes: [], rc.pd_messages: [], rc.pd_sended_nodes: [], rc.pd_received_nodes: [],
             rc.pd_convergence: [], rc.pd_convergence_frame: [], rc.pd_success: []}
    for result in [d for d in os.listdir(algdir) if os.path.isdir(os.path.join(algdir, d))]:
        with open(os.path.join(algdir, result, rc.key_whole_result+'.json')) as f:
            whole = json.load(f)
        if whole[rc.key_result_connectivity]:
            to_pd[rc.pd_nodes].append(
                whole[rc.key_result_number_of_nodes])
            to_pd[rc.pd_messages].append(
                whole[rc.key_result_all_sended_messages])
            to_pd[rc.pd_sended_nodes].append(
                whole[rc.key_result_all_sended_nodes])
            to_pd[rc.pd_received_nodes].append(
                whole[rc.key_result_all_received_nodes])
            to_pd[rc.pd_convergence].append(
                whole[rc.key_result_convergence])
            to_pd[rc.pd_convergence_frame].append(
                whole[rc.key_result_convergence_frame])
            to_pd[rc.pd_success].append(
                whole[rc.key_result_success])
    return pd.DataFrame(to_pd)


def total_walk(dirpath: str) -> ConnectedTotal:
    to_pd = {rc.pd_delay: [], rc.pd_algorithm: [], rc.pd_nodes: [],
             rc.pd_messages: [], rc.pd_sended_nodes: [], rc.pd_received_nodes: [],
             rc.pd_convergence: [], rc.pd_convergence_frame: [], rc.pd_success: []}
    for current, _dirs, files in os.walk(dirpath):
        for whole in (f for f in files if f == (rc.key_whole_result + '.json')):
            with open(os.path.join(current, whole)) as f:
                whole_dic = json.load(f)
            to_pd[rc.pd_delay].append(
                whole_dic[rc.key_result_delay])
            to_pd[rc.pd_algorithm].append(
                whole_dic[rc.key_result_algorithm])
            to_pd[rc.pd_nodes].append(
                whole_dic[rc.key_result_number_of_nodes])
            to_pd[rc.pd_messages].append(
                whole_dic[rc.key_result_all_sended_messages])
            to_pd[rc.pd_sended_nodes].append(
                whole_dic[rc.key_result_all_sended_nodes])
            to_pd[rc.pd_received_nodes].append(
                whole_dic[rc.key_result_all_received_nodes])
            to_pd[rc.pd_convergence].append(
                whole_dic[rc.key_result_convergence])
            to_pd[rc.pd_convergence_frame].append(
                whole_dic[rc.key_result_convergence_frame])
            to_pd[rc.pd_success].append(
                whole_dic[rc.key_result_success])
    return ConnectedTotal(pd.DataFrame(to_pd))


class ConnectedTotal:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.delaytotals = {}
        for delay, df in self.df.groupby(rc.pd_delay):
            self.delaytotals[delay] = DelayTotal(df)

    def delays(self) -> List[rc.GlobalTimeDelta]:
        return list(self.delaytotals.keys())

    def delay_total(self, delay: rc.GlobalTimeDelta) -> DelayTotal:
        return self.delaytotals[delay]

    def simulated_times(self) -> pd.DataFrame:
        dflist = [self.delay_total(d).simulated_times() for d in self.delays()]
        return pd.concat(dflist)


class DelayTotal:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.means = self.df.groupby([rc.pd_delay, rc.pd_algorithm, rc.pd_nodes],
                                     as_index=False).mean()

    def delay(self) -> rc.GlobalTimeDelta:
        return list(self.df.groupby(rc.pd_delay).groups.keys())[-1]

    def _delay_str(self) -> str:
        return 'delay' + str(self.delay())

    def simulated_times(self) -> pd.DataFrame:
        count = self.df.groupby([rc.pd_delay, rc.pd_algorithm, rc.pd_nodes],
                                as_index=False).count()
        return _groupby_algorithm(count, rc.pd_convergence)

    def messages(self) -> pd.DataFrame:
        # メッセージ数
        return _groupby_algorithm(self.means, rc.pd_messages)

    def plot_massages(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.messages(), algorithms=algorithms, ax=ax)
        if savedir:
            name = self._delay_str() + rc.pd_messages + '.png'
            plt.savefig(os.path.join(savedir, name))

    def sended_nodes(self) -> pd.DataFrame:
        # 転送回数
        return _groupby_algorithm(self.means, rc.pd_sended_nodes)

    def plot_sended_nodes(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.sended_nodes(), algorithms=algorithms, ax=ax)
        if savedir:
            name = self._delay_str() + rc.pd_sended_nodes + '.png'
            plt.savefig(os.path.join(savedir, name))

    def sended_nodes_per_whole(self) -> pd.DataFrame:
        # ノード数に対する転送回数
        sendednodes = self.sended_nodes()
        return sendednodes / sendednodes.index.get_level_values(rc.pd_nodes)[:, None]

    def plot_sended_nodes_per_whole(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.sended_nodes_per_whole(), algorithms=algorithms, ax=ax)
        plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        if savedir:
            name = self._delay_str() + rc.pd_sended_nodes + 'rate.png'
            plt.savefig(os.path.join(savedir, name))

    def received_nodes(self) -> pd.DataFrame:
        # 伝達したノード数
        return _groupby_algorithm(self.means, rc.pd_received_nodes)

    def plot_received_nodes(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.received_nodes(), algorithms=algorithms, ax=ax)
        if savedir:
            name = self._delay_str() + rc.pd_received_nodes + '.png'
            plt.savefig(os.path.join(savedir, name))

    def received_nodes_per_whole(self) -> pd.DataFrame:
        # 伝達率
        receivednodes = self.received_nodes()
        return receivednodes / receivednodes.index.get_level_values(rc.pd_nodes)[:, None]

    def plot_received_nodes_per_whole(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.received_nodes_per_whole(), algorithms=algorithms, ax=ax)
        plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        if savedir:
            name = self._delay_str() + rc.pd_received_nodes + 'rate.png'
            plt.savefig(os.path.join(savedir, name))

    def convergence_frame(self) -> pd.DataFrame:
        # 収束時間
        return _groupby_algorithm(self.means, rc.pd_convergence_frame)

    def plot_convergence_frame(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.convergence_frame(), algorithms=algorithms, ax=ax)
        if savedir:
            name = self._delay_str() + rc.pd_convergence_frame + '.png'
            plt.savefig(os.path.join(savedir, name))

    def successrate(self) -> pd.DataFrame:
        # 成功率
        return _groupby_algorithm(self.means, rc.pd_success)

    def plot_successrate(self, algorithms: Set[str] = None, savedir: str = None, ax: plt.Axes = None):
        plot(self.successrate(), algorithms=algorithms, ax=ax)
        plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        if savedir:
            name = self._delay_str() + rc.pd_success + '.png'
            plt.savefig(os.path.join(savedir, name))

    def saveallgraph(self, outdir: str):
        _fig, ax = plt.subplots()
        self.plot_massages(savedir=outdir, ax=ax)
        _fig, ax = plt.subplots()
        self.plot_sended_nodes(savedir=outdir, ax=ax)
        _fig, ax = plt.subplots()
        self.plot_sended_nodes_per_whole(savedir=outdir, ax=ax)
        _fig, ax = plt.subplots()
        self.plot_received_nodes(savedir=outdir, ax=ax)
        _fig, ax = plt.subplots()
        self.plot_received_nodes_per_whole(savedir=outdir, ax=ax)
        _fig, ax = plt.subplots()
        self.plot_convergence_frame(savedir=outdir, ax=ax)
        _fig, ax = plt.subplots()
        self.plot_successrate(savedir=outdir, ax=ax)


def _groupby_algorithm(dataframe: pd.DataFrame, key: str) -> pd.DataFrame:
    dflist = []
    for algorithm, df in dataframe.groupby(rc.pd_algorithm):
        df = df[[rc.pd_delay, rc.pd_nodes, key]].set_index([rc.pd_delay,
                                                            rc.pd_nodes])
        dflist.append(df.rename(columns={key: algorithm}))
    return pd.concat(dflist, axis=1)


def _alg_marker_colors():
    return [(algorithm, marker, color) for algorithm, marker, color
            in zip(rc.algorithms, rc.plt_markers, rc.rainbow())]


def plot(df: pd.DataFrame, algorithms: Set[str] = None, ax: plt.Axes = None, **kwargs):
    ax = ax or plt.gca()
    for alg, marker, color in _alg_marker_colors():
        if algorithms == None or alg in algorithms:
            ax.plot(df.index.get_level_values(rc.pd_nodes), df[alg], label=alg,
                    marker=marker, c=color, **kwargs)
    ax.legend(ncol=(len(algorithms or rc.algorithms)+3)//4)
