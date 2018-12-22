"""
S for square
T for triangle
D for diamond
"""
from copy import deepcopy
from collections import defaultdict
DIRECTIONS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1,
                                                                           -1))
DIRECTIONSHAPES = {
    (1, 1): '↘',
    (1, 0): '↓',
    (1, -1): '↙',
    (0, 1): '→',
    (0, -1): '←',
    (-1, 1): '↗',
    (-1, 0): '↑',
    (-1, -1): '↖'
}


class Board:
    def __init__(self, board):
        self.row = len(board)
        self.col = len(board[0])

        self.board = defaultdict(dict)
        self.endpoints = defaultdict(list)
        self.passpoints = defaultdict(list)
        self.autopoints = []
        for i, line in enumerate(board, 1):
            for j, ch in enumerate(line, 1):
                if ch.isupper():
                    self.endpoints[ch].append((i, j))
                elif ch.islower():
                    self.passpoints[ch].append((i, j))
                else:
                    ch = int(ch)
                    self.autopoints.append((i, j))

                if type(ch) is int:
                    self.board[(i, j)]['key'] = 'a'
                    self.board[(i, j)]['visit'] = ch
                else:
                    self.board[(i, j)]['key'] = ch
                    self.board[(i, j)]['visit'] = 1

    @staticmethod
    def _gen_edges(shape, node, board):
        i, j = node
        for di, dj in DIRECTIONS:
            if (i + di, j + dj) not in board:
                continue

            if board[(i + di, j + dj)]['key'].lower() not in ['a', shape]:
                continue

            if board[(i + di, j + dj)]['visit'] == 0:
                continue

            yield (i + di, j + dj)

    @staticmethod
    def _diagonal(p1, p2):
        return (p1[0], p2[1]), (p2[0], p1[1])

    def genenrate_all_path(self,
                           shape,
                           start=None,
                           end=None,
                           board=None,
                           path=[],
                           remove_edges=set()):

        if start is None:
            start, end = self.endpoints[shape.upper()]
        if board is None:
            board = self.board

        # print('path: ', path, ' start: ', start, board[(2, 3)]['visit'])
        if start == end:
            path.append(end)
            if board[end]['visit'] == 1:
                if all(board[p]['visit'] == 0 for p in self.passpoints[shape]):
                    board[end]['visit'] -= 1
                    yield path, board, remove_edges
            return

        assert board[start]['visit'] > 0
        for e in self._gen_edges(shape, start, board):
            if (start, e) in remove_edges:
                continue
            tmp_board = deepcopy(board)
            tmp_path = path + [start]
            tmp_board[start]['visit'] -= 1
            tmp_remove_edges = remove_edges.copy()
            p1, p2 = self._diagonal(start, e)
            tmp_remove_edges.update([(start, e), (e, start), (p1, p2), (p2,
                                                                        p1)])

            yield from self.genenrate_all_path(shape, e, end, tmp_board,
                                               tmp_path, tmp_remove_edges)
        return

    def _print_path(self, path):
        board = [[' ' for j in range(2 * self.col - 1)]
                 for i in range(2 * self.row - 1)]

        for i in range(self.row):
            for j in range(self.col):
                board[2 * i][2 * j] = self.board[(i + 1, j + 1)]['key']

        start = path.pop(0)
        for node in path:
            board[start[0] + node[0] - 2][
                start[1] + node[1] - 2] = DIRECTIONSHAPES[(node[0] - start[0],
                                                           node[1] - start[1])]
            start = node
        print('\n'.join([''.join(line) for line in board]))
        print('=' * 30)

    def solve(self):
        for paths in self._solve():
            return paths

    def _solve(self, keys=None, board=None, remove_edges=set(), paths=[]):
        if keys is None:
            keys = list(self.endpoints.keys())

        if len(keys) == 0:
            if all(board[p]['visit'] == 0 for p in self.autopoints):
                yield paths
            return

        shape = keys.pop(0)
        for path, tmp_board, tmp_remove_edges in self.genenrate_all_path(
                shape.lower(), board=board, remove_edges=remove_edges):
            yield from self._solve(keys.copy(), tmp_board, tmp_remove_edges,
                                   paths + [path])
        return


if __name__ == '__main__':
    # while True:
    #     board = []
    #     n = int(input('number of rows: '))
    #     for _ in range(n):
    #         board.append(input())
    #     b = Board(board)
    #     b.solve()
    b = Board(['TtD', 'D3d', 't2T'])
    print(b.solve())
