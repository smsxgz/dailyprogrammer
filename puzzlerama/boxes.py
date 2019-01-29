# import collections
from copy import copy


def get_board(raw_board):
    height = len(raw_board)
    width = len(raw_board[0]) + 2

    board = dict()
    boxes = 0
    for h in range(height):
        board[(0, h)] = None
        board[(width - 1, h)] = None
        for w in range(1, width - 1):
            ch = raw_board[h][w - 1]
            if ch == ' ':
                ch = None
            else:
                boxes += 1
            board[(w, height - h - 1)] = ch
    board['boxes'] = boxes
    board['height'] = height
    board['width'] = width
    return board


def gravity(board):
    height, width = board['height'], board['width']
    for w in range(width):
        box = []
        for h in range(height):
            ch = board[(w, h)]
            if ch is not None:
                box.append(ch)
        box += [None] * (height - len(box))
        for h in range(height):
            board[(w, h)] = box[h]


def smash(board):
    height, width = board['height'], board['width']
    smash = set()
    for w in range(width):
        flag = board[(w, 0)]
        num = 0
        h = 0
        while h <= height:
            ch = board.get((w, h), None)
            if ch == flag:
                num += 1
            else:
                if num >= 3 and flag:
                    for j in range(num):
                        smash.add((w, h - j - 1))
                flag = ch
                num = 1
            h += 1

    for h in range(height):
        flag = board[(0, h)]
        num = 0
        w = 0
        while w <= width:
            ch = board.get((w, h), None)
            if ch == flag:
                num += 1
            else:
                if num >= 3 and flag:
                    for j in range(num):
                        smash.add((w - j - 1, h))
                flag = ch
                num = 1
            w += 1

    for w, h in smash:
        board[(w, h)] = None
    board['boxes'] -= len(smash)

    return len(smash) > 0


def one_step(board):
    while True:
        gravity(board)
        if not smash(board):
            break


def print_board(board):
    for h in range(board['height'] - 1, -1, -1):
        print(''.join([
            board[(w, h)] if board[(w, h)] else ' '
            for w in range(board['width'])
        ]))
    print('=' * 25)


def find_solution(board, steps=1, solution=[]):
    if steps == 0:
        if board['boxes'] == 0:
            return solution
        return

    height, width = board['height'], board['width']
    for h in range(height):
        for w in range(width - 1):
            tmp_board = copy(board)
            tmp_board[(w, h)], tmp_board[(w + 1, h)] = \
                tmp_board[(w + 1, h)], tmp_board[(w, h)]
            one_step(tmp_board)
            res = find_solution(tmp_board, steps - 1, solution + [
                ((w, h), (w + 1, h)),
            ])
            if res:
                return res

    for w in range(width):
        for h in range(height - 1):
            tmp_board = copy(board)
            tmp_board[(w, h)], tmp_board[(w, h + 1)] = tmp_board[(
                w, h + 1)], tmp_board[(w, h)]
            one_step(tmp_board)
            res = find_solution(tmp_board, steps - 1, solution + [
                ((w, h), (w, h + 1)),
            ])
            if res:
                return res
    return


if __name__ == '__main__':
    # board = get_board(['  p  ', '  y  ', ' pyy ', ' ppy ', 'pyypy', 'pypyp'])
    # board = get_board(['  y  ', ' yy  ', 'yypyp', 'ypypy', 'pyypy'])
    board = get_board(
        ['   p  ', '  rr  ', '  bbp ', ' rrbr ', ' bbrbp', 'bbppbp'])
    print_board(board)
    find_solution(board, 2)
    # solver.print_board()
