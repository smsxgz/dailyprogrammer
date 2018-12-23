"""
S for square
T for triangle
D for diamond
"""
from collections import defaultdict

DIRECTIONS = {
    (1, 1): '↘',
    (1, 0): '↓',
    (1, -1): '↙',
    (0, 1): '→',
    (0, -1): '←',
    (-1, 1): '↗',
    (-1, 0): '↑',
    (-1, -1): '↖'
}


class Node:
    def __init__(self, ch):
        if ch.isupper():
            self.shape = ch
            self.visit = 1
        elif ch.islower():
            self.shape = ch
            self.visit = 2
        else:
            self.shape = 'a'
            self.visit = 2 * int(ch)

        self.edges = []


class Board:
    def __init__(self, board):
        self.row = len(board)
        self.col = len(board[0])

        self.incomplete_nodes = self.row * self.col

        self.board = dict()
        self.endpoints = defaultdict(list)
        self.incomplete_shape_nodes = defaultdict(int)
        for i, line in enumerate(board, 1):
            for j, ch in enumerate(line, 1):
                if ch.isupper():
                    self.endpoints[ch].append((i, j))
                elif ch.islower():
                    self.incomplete_shape_nodes[ch] += 1
                n = Node(ch)
                if n.visit == 0:
                    self.incomplete_nodes -= 1
                self.board[(i, j)] = n

        self.shapes = list(self.endpoints.keys())
        self.solution = []

    def _print_path(self, path):
        board = [[' ' for j in range(2 * self.col - 1)]
                 for i in range(2 * self.row - 1)]

        for i in range(self.row):
            for j in range(self.col):
                board[2 * i][2 * j] = self.board[(i + 1, j + 1)].shape

        start = path.pop(0)
        for node in path:
            board[start[0] + node[0] - 2][start[1] + node[1] -
                                          2] = DIRECTIONS[(node[0] - start[0],
                                                           node[1] - start[1])]
            start = node
        print('\n'.join([''.join(line) for line in board]))
        print('=' * 30)

    def _get_possible_edges(self, i, j, shape=None):
        coord = (i, j)
        if shape is None:
            shape = self.board[coord].shape.lower()

        edges = []
        for di, dj in DIRECTIONS:
            new_coord = (i + di, j + dj)

            if new_coord not in self.board:
                continue

            elif shape != 'a' and self.board[new_coord].shape.lower() not in [
                    'a', shape
            ]:
                continue

            elif self.board[new_coord].visit == 0:
                continue

            if (di, dj) in self.board[coord].edges or (
                    -di, -dj) in self.board[new_coord].edges:
                continue

            coord1 = (coord[0], new_coord[1])
            coord2 = (new_coord[0], coord[1])
            if (di, -dj) in self.board[coord1].edges or (
                    -di, dj) in self.board[coord2].edges:
                continue

            edges.append((di, dj))
        return edges

    def _gen_edges(self, shape, i, j):
        tmp = self.board[(i, j)].visit
        possible_edges = self._get_possible_edges(i, j, shape)
        for di, dj in possible_edges:
            possible = len(self._get_possible_edges(i + di, j + dj))
            visit = self.board[(i + di, j + dj)].visit
            if possible < visit:
                return []
            elif possible == visit and visit > 1 and tmp == 1:
                return [(di, dj)]
        return possible_edges

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
        if src_node.visit == 0:
            if self.incomplete_shape_nodes[shape] > 0:
                return False
            self.solution.append(path + [(x, y)])
            found = self._solve()
            if found:
                return True
            self.solution.pop(-1)
            return False

        edges = self._gen_edges(shape, x, y)
        # print(path, edges, x, y)
        for dx, dy in edges:
            node = self.board[(x + dx, y + dy)]
            src_node.edges.append((dx, dy))
            src_node.visit -= 1
            if src_node.visit == 0:
                self.incomplete_nodes -= 1
                if src_node.shape == shape:
                    self.incomplete_shape_nodes[shape] -= 1
            node.visit -= 1
            if node.visit == 0:
                self.incomplete_nodes -= 1

            found = self._solve(x + dx, y + dy, shape, path + [(x, y)])
            if found:
                return True

            if src_node.visit == 0:
                self.incomplete_nodes += 1
                if src_node.shape == shape:
                    self.incomplete_shape_nodes[shape] += 1
            src_node.visit += 1
            if node.visit == 0:
                self.incomplete_nodes += 1
            node.visit += 1
            src_node.edges.pop(-1)

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
    b = Board(['ddd', 'd4d', '22d', '23d', '2D2', 'Ddd'])
    # b = Board(['TDd', 't2T', 'Ddt'])
    b._solve()
    for path in b.solution:
        b._print_path(path)
