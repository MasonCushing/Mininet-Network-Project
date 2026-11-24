
from collections import deque
import heapq


def build_graph(net):
    """Build an undirected graph from Mininet links."""
    graph = {}

    for link in net.links:
        node1 = link.intf1.node.name
        node2 = link.intf2.node.name

        graph.setdefault(node1, []).append(node2)
        graph.setdefault(node2, []).append(node1)

    return graph


def shortest_path(net, source, target):
    """Find the path with the fewest hops using BFS."""
    graph = build_graph(net)

    if source not in graph or target not in graph:
        return []

    queue = deque([(source, [source])])
    visited = {source}

    while queue:
        node, path = queue.popleft()

        if node == target:
            return path

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []


def get_link_cost(net, node1, node2):
    """
    Return the cost of traversing a link.

    Currently uses hop-based costs.
    Future versions can use measured link utilization,
    latency, or packet loss.
    """
    return 1.0


def least_cost_path(net, source, target):
    """Calculate the lowest-cost path using Dijkstra."""
    graph = build_graph(net)

    if source not in graph or target not in graph:
        return []

    distances = {
        node: float('inf') for node in graph
    }

    previous_nodes = {}

    distances[source] = 0
    priority_queue = [(0, source)]

    while priority_queue:
        current_cost, current_node = heapq.heappop(
            priority_queue
        )

        if current_cost > distances[current_node]:
            continue

        if current_node == target:
            break

        for neighbor in graph.get(current_node, []):
            edge_cost = get_link_cost(
                net, current_node, neighbor
            )

            new_cost = current_cost + edge_cost

            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous_nodes[neighbor] = current_node

                heapq.heappush(
                    priority_queue,
                    (new_cost, neighbor)
                )

    if distances[target] == float('inf'):
        return []

    path = []
    current = target

    while current != source:
        path.append(current)
        current = previous_nodes[current]

    path.append(source)

    return list(reversed(path))
