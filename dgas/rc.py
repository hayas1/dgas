from __future__ import annotations
from typing import NewType, Union, Any

import torch

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

NodeID = NewType('NodeID', Union[int, str])
MessageType = NewType('MessageType', Any)
GlobalTime = NewType('GlobalTime', int)
GlobalTimeDelta = NewType('GlobalTimeDelta', int)
Number = NewType('Number', Union[int, float])

undirected_graph = 'undirected'
directed_graph = 'directed'
undirected_multigraph = 'undirected multi'
directed_multigraph = 'directed multi'


timeout = 100


edge_key = 'data'
edge_weight = 1


node_size = 100
node_color = '#1f78b4'
node_clashed_color = '#888888'
node_shape = 'o'
node_alpha = 1.0
node_edge_width = 1.0
node_edge_color = 'k'

edge_width = 1.0
edge_color = 'k'
edge_style = 'solid'
edge_alpha = 1.0
edge_arrow = True
edge_arrow_style = '-|>'
edge_arrow_size = 10

message_size = 50
message_color = '#f1874b'
message_shape = 'o'
message_alpha = 1.0
message_edge_width = 1.0
message_edge_color = 'k'

message_zorder = 1.5


key_node_frame_log = 'frame'
key_node_id_log = 'id'
key_node_sended_log = 'sended_log'
key_node_received_log = 'received_log'

key_message_content_log = 'message'
key_sended_frame_log = 'sended_frame'
key_sended_node_log = 'to_id'
# key_sended_delay = 'delay'
key_received_frame_log = 'received_frame'
key_received_node_log = 'from_id'


key_nodes_result = 'nodes'
key_graph_result = 'graph'

animation_filename = 'animation.gif'

### MANET ###
collider_index_key = 'collider'

rand_node_vel_min = -3
rand_node_vel_max = 3

manet_node_size = 100.0
communication_radius = 250.0

field_xlen = 1600.0
field_ylen = 1000.0

min_abs_vel = 0
max_abs_vel = 10

attraction_coefficient = 0.5
attraction_power = 1

repultion_coefficient = 250.0
repultion_power = 2

wall_repultion_coefficient = 1.0
wall_repultion_power = 0.5

wall_reflection = True

key_pos_log = 'pos'
key_connectivity_log = 'connectivity'
key_first_edge_log = 'first_edge'
key_edge_added_times_log = 'edge_added'
key_edge_removed_times_log = 'edge_removed'

# vague broadcast
node_delay = 5

root_color = '#ff1321'
broadcasted_color = '#dad54a'

'#0000ff'  # base matplotlib.cm.get_cmap('brg') (n=8)
bft_edge_color = '#4000bf'
mst_edge_color = '#80007f'
bftmst_edge_color = '#c0003f'
hop_edge_color = '#fe0100'
gthop_edge_color = '#be4100'
far_edge_color = '#7e8100'
area_edge_color = '#3ec100'
colored_edge_width = 3.0

key_broadcasted_frame_log = 'broadcasted_frame'
key_number_of_sended_log = 'number_of_sended'

key_whole_result = 'whole'
key_result_algorithm = 'algorithm'
key_result_number_of_nodes = 'nodes'
key_result_simulate_terminate_frame = 'frames'
key_result_delay = 'delay'
key_result_all_sended_messages = 'sended'
key_result_all_received_messages = 'received'
key_result_all_sended_nodes = 'sendednodes'
key_result_all_sended_nodes_per_whole = 'sendednodesrate'
key_result_all_received_nodes = 'receivednodes'
key_result_all_received_nodes_per_whole = 'receivednodesrate'
key_result_connectivity = 'connectivity'
key_result_convergence = 'convergence'
key_result_convergence_frame = 'convergenceframe'
key_result_success = 'success'

key_field_result = 'field'


algorithms = ['flooding', 'bft', 'mst', 'bftmst',
              'hop', 'gthop', 'far', 'area']
(algname_flooding, algname_bft, algname_mst, algname_bftmst,
 algname_hop, algname_gthop, algname_far, algname_area) = algorithms
# algname_flooding = algorithms[0]
# algname_bft = algorithms[1]
# algname_mst = algorithms[2]
# algname_bftmst = algorithms[3]
# algname_hop = algorithms[4]
# algname_gthop = algorithms[5]
# algname_far = algorithms[6]
# algname_area = algorithms[7]

pd_delay = 'delay'
pd_algorithm = 'algorithm'

pd_nodes = 'nodes'
pd_messages = 'messages'
pd_sended_nodes = 'sendednodes'
pd_received_nodes = 'receivednodes'
pd_convergence = 'convergence'
pd_convergence_frame = 'convergenceframe'
pd_success = 'success'
pd_simulated_times = 'times'

plt_markers = ['o', '*', 'p', 'h', '^', 'v', 'D', 'x']
(plt_flooding_marker, plt_bft_marker, plt_mst_marker, plt_bftmst_marker,
 plt_hop_marker, plt_gthop_marker, plt_far_marker, plt_area_marker) = plt_markers
# plt_flooding_marker = 'o'
# plt_bft_marker = '*'
# plt_mst_marker = 'p'
# plt_bftmst_marker = 'h'
# plt_hop_marker = '^'
# plt_gthop_marker = 'v'
# plt_far_marker = 'D'
# plt_area_marker = 'x'


def rainbow():
    from matplotlib import cm
    n = len(algorithms)
    rainbow = cm.get_cmap('brg')
    for i in range(n):
        yield rainbow(i/n)
