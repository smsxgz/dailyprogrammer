class Node:
    def __init__(self, ch):
        if ord(ch) == 48 or ord(ch) == 49:
            self.key = 'a'
            self.state = ord(ch) - 48
            self.range = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        elif ch == 'x':
            self.key = 'x'
            self.state = 0
            self.range = []

        elif ch.lower() == 'v':
            self.key = 'v'
            self.state = int(ch.isupper())
            self.range = [(-1, 0), (1, 0)]

        elif ch.lower() == 'h':
            self.key = 'h'
            self.state = int(ch.isupper())
            self.range = [(0, -1), (0, 1)]

        elif ch.lower() == 'y':
            self.key = 'y'
            self.state = int(ch.isupper())
            self.range = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        else:
            raise Exception('Not supported key!')

    def change(self, hard=False):
        if self.key == 'x' or (self.key == 'y' and not hard):
            pass
        else:
            self.state = 1 - self.state

    def __repr__(self):
        # return self.key + str(self.state)
        return str(self.state)


class Board:
    def __init__(self, board):
        self.row = len(board)
        self.col = len(board[0])

        self.board = [[None for _ in range(self.col)] for _ in range(self.row)]
        for i, line in enumerate(board):
            for j, ch in enumerate(line.strip()):
                self.board[i][j] = Node(ch)

    def button(self, i, j):
        n = self.board[i][j]

        n.change(hard=True)
        for x, y in n.range:
            ix, jy = i + x, j + y
            if self._check_valid_node(ix, jy):
                self.board[ix][jy].change()

    def _check_valid_node(self, i, j):
        return i >= 0 and j >= 0 and i < self.row and j < self.col

    def _check_state(self, i, j):
        flag = True
        if i > 0:
            flag &= (self.board[i - 1][j].state == 0)
        if i == self.row - 1 and j > 0:
            flag &= (self.board[i][j - 1].state == 0)
        if i == self.row - 1 and j == self.col - 1:
            flag &= self.board[i][j].state == 0

        return flag

    def solve(self, start=0, nodes=[]):
        if start == self.row * self.col:
            yield nodes
            return

        i, j = divmod(start, self.col)

        if self._check_state(i, j):
            yield from self.solve(start + 1, nodes)

        if self.board[i][j].key != 'x':
            self.button(i, j)
            if self._check_state(i, j):
                yield from self.solve(start + 1, nodes + [(i, j)])
            self.button(i, j)


def main(txt):
    with open(txt, 'r') as f:
        b = []
        for line in f.readlines():
            b.append(line.strip())

        b = Board(b)
        for nodes in b.solve():
            print(nodes)


if __name__ == '__main__':
    main('problems/problem7.txt')
