from collections import deque
from snmp_monitor import get_node_stats
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
    queue = deque([(source, [source])])
    visited = set()

    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
    return[]

def get_cost(net, node_name):
    try:
        if not node.name.startswith("h"):
            return 1
        node = net.get(node_name)
        stats = get_node_stats(node)
        bytes_total = (stats["bytes_in"] + stats["bytes_out"])
        errors_total = (stats["errors_in"] + stats["errors_out"])
        cost = (1+(bytes_total/10000000)+(errors_total*5))
        return cost
    except Exception:
        return 1

def least_cost_path(net, source, target):
    graph = build_graph(net)
    distances = {node: float('inf') for node in graph}
    previous_nodes = {}
    distances[source]=0
    pq = [(0, source)]
    while pq:
        current_cost, current_node = heapq.heappop(pq)
        if current_node == target:
            break
        for neighbor in graph.get(current_node, []):
            edge_cost = get_cost(net, neighbor)
            new_cost=(current_cost+edge_cost)
            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))
    path = []
    current = target
    while current in previous_nodes:
        path.insert(0, current)
        current = previous_nodes[current]
    path.insert(0, source)
    return path
