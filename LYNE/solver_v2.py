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
            self.shape = ch.lower()
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

        self.board = defaultdict(dict)
        self.endpoints = defaultdict(list)
        for i, line in enumerate(board, 1):
            for j, ch in enumerate(line, 1):
                if ch.isupper():
                    self.endpoints[ch].append((i, j))
                n = Node(ch)
                if n.visit == 0:
                    self.incomplete_nodes -= 1
                self.board[(i, j)] = n

        self.shapes = list(self.endpoints.keys())
        self.solution = []

    def _gen_edges(self, shape, i, j):
        coord = (i, j)
        for di, dj in DIRECTIONS:
            new_coord = (i + di, j + dj)

            if new_coord not in self.board:
                continue

            elif self.board[new_coord].shape not in ['a', shape]:
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

            yield di, dj

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
            self.solution.append(path + [(x, y)])
            found = self._solve()
            if found:
                return True
            self.solution.pop(-1)
            return False

        for dx, dy in self._gen_edges(shape, x, y):
            node = self.board[(x + dx, y + dy)]
            src_node.edges.append((dx, dy))
            src_node.visit -= 1
            if src_node.visit == 0:
                self.incomplete_nodes -= 1
            node.visit -= 1
            if node.visit == 0:
                self.incomplete_nodes -= 1

            found = self._solve(x + dx, y + dy, shape, path + [(x, y)])
            if found:
                return True

            if src_node.visit == 0:
                self.incomplete_nodes += 1
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
    b = Board(['S22ss', 'D33ss', 'd32TS', 'Dt2tT'])
    b._solve()
    print(b.solution)
