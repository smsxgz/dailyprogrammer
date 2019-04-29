from board import Position, Board

WALL = set(['#'])
PLAYER = set(['@', '+'])
GOAL = set(['.', '+', '*'])
BOX = set(['$', '*'])


def load_map(file_name):
    walls, goals = set(), set()
    boxes, player = set(), None

    with open(file_name, 'r') as f:
        num_lines = int(f.readline())

        for y, line in enumerate(f.readlines()):
            if line:
                for x, char in enumerate(line):
                    pos = Position(x, y)

                    if char in WALL:
                        walls.add(pos)
                    if char in GOAL:
                        goals.add(pos)
                    if char in BOX:
                        boxes.add(pos)
                    if char in PLAYER:
                        player = pos
            else:
                break

    board = Board(num_lines, walls, goals)
    return board, boxes, player
