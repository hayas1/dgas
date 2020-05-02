from __future__ import annotations
from typing import NewType, List, Tuple, Dict, Union


from dgas import rc, node, message


class NodeRecord:
    def __init__(self, identifier: rc.NodeID):
        self.identifier = identifier
        self.frame = 0
        self.sended_message: List[MessageRecord] = []
        self.received_message: List[MessageRecord] = []

    def to_dict(self) -> Dict[str, Any]:
        return {rc.key_node_id_log: self.identifier,
                rc.key_node_frame_log: self.frame,
                rc.key_node_sended_log: [msglog.to_sended_dict() for msglog in self.sended_message],
                rc.key_node_received_log: [msglog.to_received_dict() for msglog in self.received_message]}


class MessageRecord:
    def __init__(self, frame: rc.GlobalTime, opposite: node.Node, msg: rc.MessageType):
        self.frame = frame
        self.opposite = opposite
        self.msg = msg

    def to_sended_dict(self) -> Dict[str, Any]:
        return {rc.key_sended_frame_log: self.frame,
                rc.key_sended_node_log: self.opposite.identifier,
                rc.key_message_content_log: self.msg, }

    def to_received_dict(self) -> Dict[str, Any]:
        return {rc.key_received_frame_log: self.frame,
                rc.key_received_node_log: self.opposite.identifier,
                rc.key_message_content_log: self.msg}


class GraphRecord:
    # TODO networkxのシリアライズ機能を使えるかもしれない
    pass
    # def __init__(self):
    #     self.number_of_added_edges = 0
    #     self.number_of_removed_edges = 0

    # def to_dict(self) -> Dict[str, Any]:
    #     return {rc.key_edge_added_times: self.number_of_added_edges,
    #             rc.key_edge_removed_times: self.number_of_removed_edges}


class DrawRecord:
    # TODO 描画情報の記録
    pass


class FieldRecord:
    def __init__(self):
        self.pos: List[List[List[float]]] = []
        self.connectivity: List[bool] = []
        self.first_edges = 0
        self.added_edges = 0
        self.removed_edges = 0

    def to_dict(self) -> Dict[str, Any]:
        return {rc.key_first_edge_log: self.first_edges,
                rc.key_edge_added_times_log: self.added_edges,
                rc.key_edge_removed_times_log: self.removed_edges,
                rc.key_connectivity_log: self.connectivity,
                rc.key_pos_log: self.pos}
