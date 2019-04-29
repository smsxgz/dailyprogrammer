class Position:
    def __init__(self, cord_x, cord_y):
        self.x = cord_x
        self.y = cord_y

    def __add__(self, pos_2):
        return Position(self.x + pos_2.x, self.y + pos_2.y)

    def __str__(self):
        return "({},{})".format(self.x, self.y)

    def __repr__(self):
        return "({},{})".format(self.x, self.y)

    def __eq__(self, pos_2):
        return self.x == pos_2.x and self.y == pos_2.y

    def __ne__(self, pos_2):
        return self.x != pos_2.x or self.y != pos_2.y

    def __hash__(self):
        return hash((self.x, self.y))

    def dist(self, pos_2):
        return abs(self.x - pos_2.x) + abs(self.y - pos_2.y)


DIRECTION = [Position(0, -1), Position(0, 1), Position(1, 0), Position(-1, 0)]


class Board:
    def __init__(self, num_lines, walls, goals):
        self.num_lines = num_lines
        self.walls = walls
        self.goals = goals

        self.pull_reachable = self._detect_simple_deadlock()

    def moves_available(self, boxes, player):
        moves_available = []
        stack = [player]
        norm_pos = player
        mem = set()

        while stack:
            player = stack.pop(0)
            mem.add(player)
            if player.y < norm_pos.y:
                norm_pos = player
            elif player.y == norm_pos.y and player.x < norm_pos.x:
                norm_pos = player

            for d in DIRECTION:
                new_pos = player + d
                if new_pos in mem or new_pos in self.walls:
                    continue
                elif new_pos in boxes:
                    new_box_pos = new_pos + d
                    if new_box_pos not in self.walls.union(
                            boxes) and new_box_pos in self.pull_reachable:
                        moves_available.append((new_pos, d))
                else:
                    stack.append(new_pos)

        return moves_available, norm_pos, mem

    def is_finished(self, boxes):
        return len(self.goals.difference(boxes)) == 0

    def _detect_simple_deadlock(self):
        """Squares which can be visited by pulling from goals."""
        stack = list(self.goals)
        visited = set()

        while stack:
            pos = stack.pop(0)
            visited.add(pos)

            for d in DIRECTION:
                new_pos = pos + d
                if any([
                        new_pos in visited, new_pos in self.walls,
                        new_pos + d in self.walls
                ]):
                    continue
                else:
                    stack.append(new_pos)
        return visited

    # def freeze_deadlock(self, boxes, player):
    #     res = {}

    def print_board(self, boxes, player):
        """
        Returns a string representation like the input files
        """
        str_board = []
        for y in range(self.num_lines):
            str_board.append([' '] * 20)  # 20 is an abitrary width

        for wall in self.walls:  # walls
            str_board[wall.y][wall.x] = '#'

        for box in boxes.difference(self.goals):  # boxes - goals
            str_board[box.y][box.x] = '$'

        for box in self.goals.intersection(boxes):  # boxes & goals
            str_board[box.y][box.x] = '*'

        for goal in self.goals.difference(boxes):  # goals - boxes
            str_board[goal.y][goal.x] = '.'

        if player in self.goals:  # player on goal
            str_board[player.y][player.x] = '+'
        else:  # player off goal
            str_board[player.y][player.x] = '@'

        print('\n'.join([''.join(line) for line in str_board]))
