from .stateset import StateSet


def breadth_first_search(board, boxes, player):

    stack = [(frozenset(boxes), player, [])]
    state_info_cache = StateSet()

    while stack:
        boxes, player, path = stack.pop(0)

        moves, norm_pos, reachable = board.moves_available(boxes, player)
        state_info_cache.update(boxes, norm_pos, reachable)

        for new_pos, d in moves:
            new_boxes = set(boxes)
            new_boxes.remove(new_pos)
            new_boxes.add(new_pos + d)
            new_boxes = frozenset(new_boxes)

            if (new_boxes, new_pos) in state_info_cache:
                continue
            elif board.is_finished(new_boxes):
                return path + [(new_pos, d)]
            else:
                # board.print_board(new_boxes, new_pos)
                stack.append((new_boxes, new_pos, path + [(new_pos, d)]))
