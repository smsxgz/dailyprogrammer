from colorama import init, deinit, Fore, Back, Style

init()

BLACK = Fore.BLACK

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


def print_board(grid, size, color=False):
    width, height = size
    if color:
        board = ''
        for y in range(height):
            print(''.join([grid[(x, y)] for x in range(width)]))


if __name__ == '__main__':
    # from collections import defaultdict
    # pentominos = defaultdict(dict)
    variations = {}
    for name in PENTOMINOS:
        variations[name] = variation(PENTOMINOS[name]['variations'])
