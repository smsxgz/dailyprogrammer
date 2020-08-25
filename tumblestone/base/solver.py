from collections import defaultdict


def available_move(board, color=None, ban_color='z', cache=[]):
    if len(cache) == 3:
        yield color, cache, board
        return

    if cache:
        for i in range(cache[-1], len(board)):
            line = board[i]
            if len(line) > 0 and line[0] == color:
                tmp_board = board.copy()
                tmp_board[i] = line[1:]
                yield from available_move(tmp_board,
                                          color=color,
                                          cache=cache + [i])
        return

    else:
        for i in range(len(board)):
            line = board[i]
            if len(line) > 0 and line[0] != ban_color:
                tmp_board = board.copy()
                tmp_board[i] = line[1:]
                yield from available_move(tmp_board, color=line[0], cache=[i])
        return


def hash_board(board, ban_color):
    return '\n'.join(board + [ban_color])


def is_terminal(board):
    return not any(line for line in board)


def dfs(board):
    mem = {hash_board(board, 'z')}
    stack = [[board, 'z', []]]

    while stack:
        board, ban, solution = stack.pop(-1)
        for c, step, b in available_move(board, ban_color=ban):
            if is_terminal(b):
                print(solution + [step])
                return

            key = hash_board(b, c)
            if key in mem:
                continue
            else:
                mem.add(key)
                stack.append([b, c, solution + [step]])


if __name__ == '__main__':
    with open('boards/example.txt', 'r') as f:
        board = []
        for line in f.readlines():
            board.append(line.strip())

    dfs(board)
