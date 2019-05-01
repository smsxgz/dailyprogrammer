from .stateset import StateSet
from .Aaster_fibonacci_heap import FibonacciHeap

import numpy as np
from scipy.optimize import linear_sum_assignment


def heuristic(goals, boxes):
    goals, boxes = list(goals), list(boxes)
    assert len(goals) == len(boxes)

    dists = np.array([[b.dist(g) for g in goals] for b in boxes])
    row_ind, col_ind = linear_sum_assignment(dists)

    return dists[row_ind, col_ind].sum()


def reconstruct_path(cameFrom, current):
    total_path = [current]
    while current in cameFrom:
        current = cameFrom[current]
        total_path.append(current)
    return total_path


def Astar_search(board, boxes, player):
    moves, norm_pos, reachable = board.moves_available(boxes, player)

    openset = FibonacciHeap()
    openset.add(
        frozenset(boxes), norm_pos, reachable, moves, 0,
        heuristic(board.goals, boxes))

    closedset = StateSet()
    camefrom = dict()

    while not openset.is_empty:
        state_info = openset.pop()
        closedset.update(state_info['boxes'], state_info['norm_pos'],
                         state_info['reachable'])

        tentative_gscore = state_info['gscore'] + 1

        for new_pos, d in state_info['moves']:
            boxes = set(state_info['boxes'])
            boxes.remove(new_pos)
            boxes.add(new_pos + d)
            boxes = frozenset(boxes)

            if (boxes, new_pos) in closedset:
                continue
            elif board.is_finished(boxes):
                return [(boxes, new_pos)] + reconstruct_path(
                    camefrom, (state_info['boxes'], state_info['norm_pos']))

            # if not boxes.difference(
            #         set([Position(2, 6),
            #              Position(2, 4),
            #              Position(4, 3)])):
            #     from IPython import embed
            #     embed()

            norm_pos = openset.look_up((boxes, new_pos))
            if norm_pos is None:
                moves, norm_pos, reachable = board.moves_available(
                    boxes, new_pos)
                # print(moves, boxes, new_pos)
                openset.add(boxes, norm_pos, reachable, moves,
                            tentative_gscore, heuristic(board.goals, boxes))
            elif tentative_gscore >= openset.get_gscore((boxes, norm_pos)):
                continue

            openset.decreaseKey((boxes, norm_pos), tentative_gscore)
            camefrom[(boxes, norm_pos)] = (state_info['boxes'],
                                           state_info['norm_pos'])
