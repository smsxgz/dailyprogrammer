from colorama import init, deinit, Fore, Back, Style

init()

PENTOMINOS = {
    'F': {
        'variations': ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0)),
        'color': Fore.YELLOW + Style.BRIGHT
    },
    'I': {
        'variations': ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        'color': Fore.WHITE
    },
    'L': {
        'variations': ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
        'color': Fore.WHITE + Style.BRIGHT
    },
    'N': {
        'variations': ((0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
        'color': Fore.RED + Style.DIM
    },
    'P': {
        'variations': ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        'color': Style.BRIGHT + Fore.GREEN
    },
    'T': {
        'variations': ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0)),
        'color': Fore.YELLOW
    },
    'U': {
        'variations': ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
        'color': Fore.BLUE
    },
    'V': {
        'variations': ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
        'color': Fore.MAGENTA
    },
    'W': {
        'variations': ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        'color': Fore.CYAN
    },
    'X': {
        'variations': ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        'color': Fore.RED + Style.BRIGHT
    },
    'Y': {
        'variations': ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3)),
        'color': Fore.BLUE + Style.BRIGHT
    },
    'Z': {
        'variations': ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
        'color': Fore.MAGENTA + Style.BRIGHT
    },
    '.': {
        'color': Fore.BLACK,
    },
    ' ': {
        'color': Fore.BLACK,
    }
}


def reset(positions):
    """

    This is used for setup before starting the search
    Moves the shape's position so that the top left square is at (0, 0)

    """

    min_x, min_y = min(positions, key=lambda x: x[::-1])

    return tuple(sorted((x - min_x, y - min_y) for x, y in positions))


def variation(positions):
    """

    This is used for setup before starting the search
    Returns unique rotations and reflections of the shape

    """

    return list({
        reset(var)
        for var in (
            positions,
            [(-y, x) for x, y in positions],  # Anti-clockwise 90
            [(-x, -y) for x, y in positions],  # 180
            [(y, -x) for x, y in positions],  # Clockwise 90
            [(-x, y) for x, y in positions],  # Mirror vertical
            [(-y, -x) for x, y in positions],  # Mirror diagonal
            [(x, -y) for x, y in positions],  # Mirror horizontal
        )
    })


for name in PENTOMINOS:
    if name in ['.', ' ']:
        continue
    PENTOMINOS[name]['variations'] = variation(PENTOMINOS[name]['variations'])


def print_board(grid, size, color=False):
    width, height = size
    if color:
        board = (Style.RESET_ALL + '\n').join([
            ''.join([
                PENTOMINOS[grid[(x, y)]]['color'] + "██" + Style.RESET_ALL
                for x in range(width)
            ]) for y in range(height)
        ])
    else:
        board = '\n'.join([
            ''.join([grid[(x, y)] for x in range(width)])
            for y in range(height)
        ])

    print(board + '\n')


def solve(grid, size, available_shapes, start=0):
    if all(v != "." for v in grid.values()):
        yield grid
        return

    width, height = size

    for i in range(start, width * height):
        y, x = divmod(i, width)
        if grid[(x, y)] == '.':
            for name in available_shapes:
                for shape_var in PENTOMINOS[name]['variations']:
                    if all(
                            grid.get((x + xs, y + ys)) == "."
                            for xs, ys in shape_var):
                        temp_grid = grid.copy()
                        temp_shapes = available_shapes.copy()
                        for xs, ys in shape_var:
                            temp_grid[(x + xs, y + ys)] = name
                        temp_shapes.remove(name)

                        yield from solve(temp_grid, size, temp_shapes, i + 1)
            return


def main():
    width, height = list(
        map(int,
            input('Enter the board size: (width <= height)\nwidth  height\n')
            .split(' ')))

    assert width <= height

    holes = []
    if width == 8 and height == 8:
        print('Enter the position of holes:')
        for _ in range(4):
            h = list(map(int, input().split(' ')))
            assert h[0] < width and h[0] >= 0
            assert h[1] < height and h[1] >= 0
            holes.append(h)

    grid = {(x, y): "." for x in range(width) for y in range(height)}
    for x, y in holes:
        grid[(x, y)] = " "

    shapes = [name for name in PENTOMINOS if name not in ['.', ' ']]

    FLAG = False
    for solution in solve(grid, (width, height), shapes):
        print_board(solution, (width, height), color=True)
        FLAG = True
        # break
    if not FLAG:
        # else:
        print("No solution")


if __name__ == '__main__':
    main()
