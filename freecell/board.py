from bisect import bisect


def deepcopy(lst):
    return [l[:] for l in lst]


DICT1 = {'s': 0, 'h': 1, 'c': 2, 'd': 3}
DICT2 = {0: 's', 1: 'h', 2: 'c', 3: 'd'}


def str2id(card_str):
    return (DICT1[card_str[0]]) + (int(card_str[1:]) << 2)


def id2str(card_id):
    return DICT2[card_id & 3] + str(card_id >> 2)


def hash_board(board):
    s = ''
    for line in board:
        s += ''.join(id2str(c) for c in line) + '\n'
    return s


def print_board(board):
    s = 'Goals: {}\n'.format([id2str(c - 4) for c in board[0]])
    s += 'Freecells: {}\n'.format([id2str(c) for c in board[1]])

    for line in board[2:]:
        s += ','.join(id2str(c) for c in line) + '\n'
    print(s)


def is_valid(c1, c2):
    # c1 -> c2
    return c2 // 4 + 1 == c1 // 4 and c1 % 2 != c2 % 2


def valid_moves(board):
    goals = board[0]
    freecells = board[1]
    board = board[2:]

    m = len(board)
    empty = 8 - m

    moves = (5 - len(freecells)) * 2**empty

    # from Freecell to Goal
    for i in range(len(freecells)):
        c = freecells[i]
        if c in goals:
            tmp_goals = goals.copy()
            tmp_goals[c & 3] += 4
            yield [tmp_goals, freecells[:i] + freecells[i + 1:]
                   ] + board, f'Move {id2str(c)} to Goal'

    # from board to goals
    for j in range(m):
        line = board[j]
        c = line[-1]
        if c in goals:
            tmp_board = deepcopy(board)
            tmp_board[j].pop(-1)
            if len(tmp_board[j]) == 0:
                tmp_board = tmp_board[:j] + tmp_board[j + 1:]
            tmp_goals = goals.copy()
            tmp_goals[c & 3] += 4
            yield [tmp_goals, freecells
                   ] + tmp_board, f'Move {id2str(c)} to Goal'

    # from freecells to board
    for i in range(len(freecells)):
        c = freecells[i]
        for k in range(m):
            line = board[k]
            if is_valid(line[-1], c):
                tmp_board = deepcopy(board)
                tmp_board[k].append(c)
                yield [
                    goals, freecells[:i] + freecells[i + 1:]
                ] + tmp_board, f'Move {id2str(c)} after {id2str(line[-1])}'

        # to an empty line
        if empty > 0:
            tmp_board = deepcopy(board)
            k = bisect([line[0] for line in board], c)
            tmp_board = tmp_board[:k] + [[c]] + tmp_board[k:]
            yield [goals, freecells[:i] + freecells[i + 1:]
                   ] + tmp_board, f'Move {id2str(c)} to an empty line'

    # from board to board
    for j in range(m):
        line = board[j]
        idx = len(line) - 1
        while len(line) - idx <= moves:
            c = line[idx]
            for k in range(m):
                if k != j and is_valid(board[k][-1], c):
                    tmp_board = deepcopy(board)
                    tmp_board[k] += line[idx:]
                    tmp_board[j] = line[:idx]
                    if idx == 0:
                        tmp_board = tmp_board[:j] + tmp_board[j + 1:]

                    yield [
                        goals, freecells
                    ] + tmp_board, f'Move {id2str(c)} after {id2str(board[k][-1])}'

            if empty > 0 and idx > 0 and (len(line) - idx) <= (moves // 2):
                tmp_board = deepcopy(board)
                tmp_board[j] = line[:idx]
                k = bisect([ln[0] for ln in board], c)
                tmp_board = tmp_board[:k] + [line[idx:]] + tmp_board[k:]
                yield [goals, freecells
                       ] + tmp_board, f'Move {id2str(c)} to an empty line'

            if idx == 0 or not is_valid(line[idx - 1], c):
                break
            idx -= 1

    # from board to freecell
    if len(freecells) < 4:
        for j in range(m):
            tmp_board = deepcopy(board)
            c = tmp_board[j].pop(-1)
            if len(tmp_board[j]) == 0:
                tmp_board = tmp_board[:j] + tmp_board[j + 1:]

            tmp_freecells = freecells + [c]
            tmp_freecells.sort()
            yield [goals, tmp_freecells
                   ] + tmp_board, f'Move {id2str(c)} to freecell'
