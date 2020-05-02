from __future__ import annotations
from typing import Iterable, Iterator, Generator, Callable, Any

from dgas import rc


def global_time(untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None) -> Generator[rc.GlobalTime, None, None]:
    t = 0
    while True:
        yield t
        t += 1
        if timeout != None and t > timeout:
            return
        if (untiltime != None and t > untiltime) and (timeout == None or timeout > untiltime):
            return


def loop(untiltime: rc.GlobalTime = None, timeout: rc.GlobalTime = None,
         condition: Callable[[Any], bool] = lambda x: False, conditionarg: Any = None,
         eachloop: Callable[[Any], Any] = lambda x: None, eachlooparg: Any = None,
         timeeachlooparg=False, eachloopreturn=False):
    returns = []
    for t in global_time(untiltime, timeout):
        eachlooparg = t if timeeachlooparg else eachlooparg
        if eachloopreturn:
            returns.append(eachloop(eachlooparg))
        else:
            eachloop(eachlooparg)
        condition_satisfied = condition(conditionarg)
        if (untiltime == None or untiltime < t) and condition_satisfied:
            break
    return returns if eachloopreturn else None

# def loop(timeout_and_condition=True, timeout=None,
#          condition: Callable[[Any], bool] = lambda x: False, conditionarg: Any = None,
#          eachloop: Callable[[Any], Any] = lambda x: None, eachlooparg: Any = None,
#          timeeachlooparg=False, eachloopreturn=False):
#     time_iterator = global_time(timeout)
#     timeout_flag, condition_flag = False, False
#     returns = []
#     while True:
#         try:
#             t = next(time_iterator)
#         except StopIteration:
#             timeout_flag = True
#         eachlooparg = t if timeeachlooparg else eachlooparg
#         if eachloopreturn:
#             returns.append(eachloop(eachlooparg))
#         else:
#             eachloop(eachlooparg)
#         condition_flag = condition(conditionarg)
#         if timeout_and_condition and timeout_flag and condition_flag:
#             return returns if eachloopreturn else None
#         elif not timeout_and_condition and (timeout_flag or condition_flag):
#             return returns if eachloopreturn else None
