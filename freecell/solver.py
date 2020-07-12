from board import valid_moves, hash_board, str2id, print_board


def dfs(board):
    mem = {hash_board(board)}
    # count = 1
    # max_goal = sum(board[0])
    stack = [[board, []]]

    while stack:
        board, solution = stack.pop(-1)
        # count += 1

        # if count % 10000 == 0:
        # print(count, max_goal, len(mem))
        # print_board(board)

        for b, move in list(valid_moves(board))[::-1]:
            if hash_board(b) in mem:
                continue
            if sum(b[0]) == 230:
                print(b[0])
                return solution + [move]

            mem.add(hash_board(b))
            # max_goal = max(sum(b[0]), max_goal)

            stack.append([b, solution + [move]])


if __name__ == '__main__':
    with open('boards/1887942.txt', 'r') as f:
        board = []
        for line in f.readlines():
            board_line = []
            for ch in line.strip().split(' '):
                board_line.append(str2id(ch))
            board.append(board_line)
    board.sort(key=lambda x: x[0])
    board = [list(range(4, 8)), []] + board

    print_board(board)
    for idx, solution in enumerate(dfs(board)):
        print(idx, solution)
