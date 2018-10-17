"""
    This module will find the shortest path between two points
    """
from heapq import heappush, heappop
import numpy as np
from game_map import GameMap

def heuristic(point_a, point_b):
    """
        Manhattan distance heuristic function. Used by the A* algorithm
        """
    return (point_b[0] - point_a[0]) ** 2 + (point_b[1] - point_a[1]) ** 2

def build_path(came_from, goal):
    """
        Build the path based on the path found from the A* algorithm
        """
    path = [goal]
    current = goal

    while current in came_from:
        current = came_from[current]
        path.insert(0, current)

    # Remove the start from the path
    path = path[1::]

    return path

def get_path(game_map, start, goal):
    """
        Implementation of the A* algorithm to find the shortest path
        between two points in the map.
        """
    np.set_printoptions(threshold=np.inf)
    # The set of nodes already evaluated
    closed_set = set()

    # For each node, which node it can most efficiently be reached from.
    # If a node can be reached from many nodes, came_from will eventually contain the
    # most efficient previous step.
    came_from = dict()

    # For each node, the cost of getting from the start node to that node.
    # The cost of going from start to start is zero.
    g_score = {start: 0}

    # For each node, the total cost of getting from the start node to the goal
    # by passing by that node. That value is partly known, partly heuristic.
    # For the first node, that value is completely heuristic.
    f_score = {start: heuristic(start, goal)}

    # The set of currently discovered nodes that are not evaluated yet.
    # Initially, only the start node is known.
    open_heap = []
    heappush(open_heap, (f_score[start], start))

    while open_heap:
        # Current it the node in openSet having the lowest f_score[] value
        current = heappop(open_heap)[1]

        # We have arrived at our destination
        if current == goal:
            return build_path(came_from, current)

        # Mark this one as visited
        closed_set.add(current)

        # Find the neighbours of the current cell
        neighbours = [(current[0], current[1]+1), (current[0], current[1]-1),
                        (current[0] + 1, current[1]), (current[0]-1, current[1])]

        # Go through each neightbor
        for neighbour in neighbours:
            # Ignore the neighbour which is already evaluated.
            if neighbour in closed_set:
                continue

            # Ignore neighbours that do not exist
            dimensions = game_map.shape
            if not 0 <= neighbour[0] < dimensions[0] or not 0 <= neighbour[1] < dimensions[1]:
                continue

            # Only allow neighbours with value less than inaccessible
            if game_map[neighbour] >= GameMap.TILES.INACCESSIBLE.value:
                continue

            # The distance from start to a neighbour
            tentative_g_score = g_score[current] + 1

            # This is not a better path
            if neighbour in g_score and tentative_g_score >= g_score[neighbour]:
                continue

            g_score[neighbour] = tentative_g_score
            f_score[neighbour] = g_score[neighbour] + \
                heuristic(neighbour, goal)

            # Discover a new node
            if neighbour not in open_heap:
                heappush(open_heap, (f_score[neighbour], neighbour))

            # This path is the best until now. Record it!
            came_from[neighbour] = current
