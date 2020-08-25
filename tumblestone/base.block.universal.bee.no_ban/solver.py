def available_move(board, block, bid=0, color=None, cache=[]):
    if len(cache) == 3:
        yield cache, board
        return

    if cache:
        for i in range(len(board)):
            line = board[i]
            if i not in block[bid] and len(line) > 0:
                if line[0] == color or line[0] == 'u':
                    tmp_board = board.copy()
                    tmp_board[i] = line[1:]
                    yield from available_move(tmp_board,
                                              block,
                                              1 - bid,
                                              color=color,
                                              cache=cache + [i])
        return

    else:
        for i in range(len(board)):
            line = board[i]
            if i not in block[bid] and len(line) > 0:
                if line[0] != 'u':
                    tmp_board = board.copy()
                    tmp_board[i] = line[1:] + line[0]
                    yield from available_move(tmp_board,
                                              block,
                                              1 - bid,
                                              color=line[0],
                                              cache=[i])
        return


def hash_board(board):
    return '\n'.join(board)


def is_terminal(board):
    return not any(line for line in board)


def dfs(board, block):
    mem = {hash_board(board)}
    stack = [[board, 0, []]]

    while stack:
        board, bid, solution = stack.pop(-1)
        for step, b in available_move(board, block, bid):
            if is_terminal(b):
                print(solution + [step])
                return

            key = hash_board(b)
            if key in mem:
                continue
            else:
                mem.add(key)
                stack.append([b, 1 - bid, solution + [step]])


if __name__ == '__main__':
    with open('boards/example.txt', 'r') as f:
        block = f.readline().strip().split(',')
        for i in range(2):
            if block[i]:
                block[i] = [int(ch) for ch in block[i].split(' ')]
            else:
                block[i] = []
        print(block)
        board = []
        for line in f.readlines():
            board.append(line.strip())

    dfs(board, block)
