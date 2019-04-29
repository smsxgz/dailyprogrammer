from collections import defaultdict


def depth_first_search(board, boxes, player):

    stack = [(frozenset(boxes), player, [])]
    state_info_cache = defaultdict(dict)

    def is_repeated(boxes, player):
        if boxes in state_info_cache:
            state_info = state_info_cache[boxes]
            for norm_pos in state_info:
                if player in state_info[norm_pos]:
                    return True
        return False

    while stack:
        boxes, player, path = stack.pop(-1)

        moves, norm_pos, reachable = board.moves_available(boxes, player)
        state_info_cache[boxes][norm_pos] = reachable

        for new_pos, d in moves:
            new_boxes = set(boxes)
            new_boxes.remove(new_pos)
            new_boxes.add(new_pos + d)
            new_boxes = frozenset(new_boxes)

            if is_repeated(new_boxes, new_pos):
                continue
            elif board.is_finished(new_boxes):
                return path + [(new_pos, d)]
            else:
                # board.print_board(new_boxes, new_pos)
                stack.append((new_boxes, new_pos, path + [(new_pos, d)]))
