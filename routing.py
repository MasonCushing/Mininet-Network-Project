from collections import deque
from snmp_monitor import get_node_stats
from Topology import ROUTER_NEXT_HOPS
from mininet_command_lock import mininet_command_lock
import heapq

def build_graph(net):
    graph={}
    for link in net.links:
        node1 = link.intf1.node.name
        node2 = link.intf2.node.name
        graph.setdefault(node1, []).append(node2)
        graph.setdefault(node2, []).append(node1)
    return graph

def shortest_path(net, source, target):
    graph = build_graph(net)
    if source not in graph or target not in graph:
        return []

    queue = deque([(source, [source])])
    visited = {source}

    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []


def get_cost(net, node_name):
    try:
        if not node_name.startswith("h"):
            return 1.0
        node = net.get(node_name)
        stats = get_node_stats(node)
        bytes_total = stats["bytes_in"] + stats["bytes_out"]
        errors_total = stats["errors_in"] + stats["errors_out"]
        return 1.0 + (bytes_total / 10000000.0) + (errors_total * 5.0)
    except Exception:
        return 1.0


def least_cost_path(net, source, target):
    graph = build_graph(net)
    if source not in graph or target not in graph:
        return []

    distances = {node: float('inf') for node in graph}
    previous_nodes = {}
    distances[source] = 0.0
    pq = [(0.0, source)]

    while pq:
        current_cost, current_node = heapq.heappop(pq)
        if current_cost != distances[current_node]:
            continue
        if current_node == target:
            break

        for neighbor in graph[current_node]:
            edge_cost = get_cost(net, neighbor)
            new_cost = current_cost + edge_cost
            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))

    if target not in previous_nodes and source != target:
        return []

    path = []
    current = target
    while True:
        path.insert(0, current)
        if current == source:
            break
        if current not in previous_nodes:
            return []
        current = previous_nodes[current]
    return path


def apply_route(net, source, target, path):
    if not path:
        raise ValueError('No path available')

    installed = []

    def install_destination(destination, route_path):
        destination_ip = net.get(destination).IP()

        for router_index, router_name in enumerate(route_path):
            if not router_name.startswith('r'):
                continue
            if router_index + 1 >= len(route_path):
                continue

            next_node = route_path[router_index + 1]
            if not next_node.startswith('r'):
                continue

            next_hop = ROUTER_NEXT_HOPS[router_name].get(next_node)
            if not next_hop:
                continue

            command = f'ip route replace {destination_ip}/32 via {next_hop}'
            with mininet_command_lock:
                net.get(router_name).cmd(command)
            installed.append({
                'router': router_name,
                'destination': destination,
                'destination_ip': destination_ip,
                'next_hop': next_hop
            })

    install_destination(target, path)
    install_destination(source, list(reversed(path)))
    return installed
