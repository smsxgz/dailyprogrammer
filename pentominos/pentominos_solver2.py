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


shapes = [(((0, 1), (1, 0), (1, 1), (1, 2), (2, 0)),
           "F"), (((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
                  "I"), (((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
                         "L"), (((0, 2), (0, 3), (1, 0), (1, 1), (1, 2)), "N"),
          (((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
           "P"), (((0, 0), (1, 0), (1, 1), (1, 2), (2, 0)),
                  "T"), (((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
                         "U"), (((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)), "V"),
          (((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
           "W"), (((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
                  "X"), (((0, 1), (1, 0), (1, 1), (1, 2), (1, 3)),
                         "Y"), (((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)), "Z")]

shape_variations = {shape: variation(shape) for shape, name in shapes}


def pprint(grid, size, transpose=False):
    """

    Function to print the grid in a nice format

    """

    width, height = size
    if transpose:
        for x in range(width):
            print("".join([grid[(x, y)] for y in range(height)]))
    else:
        for y in range(height):
            print("".join([grid[(x, y)] for x in range(width)]))


def solve(grid, size, available_shapes, start=0):
    """

    Recursive function that yields completed/solved grids
    Max recursion depth is width*height//5+1

    """

    # yield a solution if all grid values are occupied
    #if not available_shapes:
    if all(v != "." for v in grid.values()):
        yield grid
        return

    width, height = size

    # Traverse the grid left to right, then top to bottom like reading a book
    # Look for next open space (".")
    for i in range(start, width * height):
        y, x = divmod(i, width)
        if grid[(x, y)] == ".":
            for shape, name in available_shapes:
                # Check each rotation and reflection of shape
                for shape_var in shape_variations[shape]:
                    if all(
                            grid.get((x + xs, y + ys)) == "."
                            for xs, ys in shape_var):
                        temp_grid = grid.copy()
                        temp_shapes = available_shapes.copy()
                        for xs, ys in shape_var:
                            temp_grid[(x + xs, y + ys)] = name
                        temp_shapes.remove((shape, name))

                        yield from solve(temp_grid, size, temp_shapes, i + 1)

            return  # No more shapes are found, let previous recursion continue


from time import time


def main(width, height, *holes):
    """

    Program is faster when width is less than height
    if width is greater than height, swap them around

    Iterate over solve() for more solutions

    """

    t = time()
    print(width, height, *holes)

    grid = {(x, y): "." for x in range(width) for y in range(height)}
    for x, y in holes:
        grid[(x, y)] = " "

    if width > height:
        grid = {(y, x): V for (x, y), V in grid.items()}

        for solution in solve(grid, (height, width), shapes):
            pprint(solution, (height, width), True)
            break
        else:
            print("No solution")
    else:
        for solution in solve(grid, (width, height), shapes):
            pprint(solution, (width, height))
            break
        else:
            print("No solution")
    print(f"{time()-t:.3f}s\n")


main(10, 6)
main(12, 5)
main(15, 4)
main(20, 3)
main(5, 5)
main(7, 5)
main(5, 4)
main(10, 5)

main(8, 8, (3, 3), (4, 3), (3, 4), (4, 4))
main(8, 8, (0, 7), (1, 3), (2, 4), (3, 5))
main(8, 8, (1, 0), (3, 0), (0, 3), (1, 2))
