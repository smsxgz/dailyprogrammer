"""
S for square
T for triangle
D for diamond
"""
from collections import defaultdict

DIRECTIONS = {
    (1, 1): 'd',
    (1, 0): 'v',
    (1, -1): 'd',
    (0, 1): 'h',
    (0, -1): 'h',
    (-1, 1): 'd',
    (-1, 0): 'v',
    (-1, -1): 'd'
}


def get_restriction_name(dx, dy, x, y):
    x += min(0, dx)
    y += min(0, dy)
    return '{}_{}_{}'.format(DIRECTIONS[(dx, dy)], x, y)


class Board:
    def __init__(self, board):
        self.row = len(board)
        self.col = len(board[0])

        self.incomplete_nodes = self.row * self.col

        self.board = defaultdict(dict)
        self.endpoints = defaultdict(list)
        self.incomplete_shape_nodes = defaultdict(int)
        for i, line in enumerate(board, 1):
            for j, ch in enumerate(line, 1):
                if ch.isupper():
                    self.board[(i, j)]['shape'] = ch.lower()
                    self.board[(i, j)]['visit'] = 1
                    self.endpoints[ch].append((i, j))
                elif ch.islower():
                    self.board[(i, j)]['shape'] = ch
                    self.board[(i, j)]['visit'] = 2
                    self.incomplete_shape_nodes[ch] += 1
                else:
                    self.board[(i, j)]['shape'] = 'a'
                    self.board[(i, j)]['visit'] = 2 * int(ch)
                    if int(ch) == 0:
                        self.incomplete_nodes -= 1

        self.shapes = list(self.endpoints.keys())
        self.restrictions = set()
        self.solution = []

    def _gen_edges(self, shape, i, j):
        for di, dj in DIRECTIONS:
            new_coord = (i + di, j + dj)

            if new_coord not in self.board:
                continue

            elif self.board[new_coord]['shape'] not in ['a', shape]:
                continue

            elif self.board[new_coord]['visit'] == 0:
                continue

            restriction = get_restriction_name(di, dj, i, j)
            if restriction in self.restrictions:
                continue

            yield di, dj, restriction

    def _solve(self, x=None, y=None, shape=None, path=[]):
        if x is None:
            if len(self.shapes) == 0:
                if self.incomplete_nodes == 0:
                    # print('We find a solution.')
                    return True
                return False
            else:
                s = self.shapes.pop(-1)
                px, py = self.endpoints[s][0]
                found = self._solve(px, py, s.lower())
                if found:
                    return True
                self.shapes.append(s)
                return False

        src_node = self.board[(x, y)]
        if src_node['visit'] == 0:
            if self.incomplete_shape_nodes[shape] == 0:
                return False
            self.solution.append(path + [(x, y)])
            found = self._solve()
            if found:
                return True
            self.solution.pop(-1)
            return False

        for dx, dy, restriction in self._gen_edges(shape, x, y):
            node = self.board[(x + dx, y + dy)]
            src_node['visit'] -= 1
            if src_node['visit'] == 0:
                self.incomplete_nodes -= 1
                if src_node['shape'] == shape:
                    self.incomplete_shape_nodes[shape] -= 1
            node['visit'] -= 1
            if node['visit'] == 0:
                self.incomplete_nodes -= 1
            self.restrictions.add(restriction)

            found = self._solve(x + dx, y + dy, shape, path + [(x, y)])
            if found:
                return True

            if src_node['visit'] == 0:
                self.incomplete_nodes += 1
                if src_node['shape'] == shape:
                    self.incomplete_shape_nodes[shape] += 1
            src_node['visit'] += 1
            if node['visit'] == 0:
                self.incomplete_nodes += 1
            node['visit'] += 1
            self.restrictions.remove(restriction)

        return False

    def solve(self):
        self._solve()
        return self.solution


if __name__ == '__main__':
    # while True:
    #     board = []
    #     n = int(input('number of rows: '))
    #     for _ in range(n):
    #         board.append(input())
    #     b = Board(board)
    #     b.solve()
    b = Board(['ssss', 's3Ss', 'd32s', 'd23S', 'd2dd', 'dDdD'])
    b._solve()
    print(b.solution)
