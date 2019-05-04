from load_map import load_map
from algorithms.Astar import Astar_search

board, boxes, player = load_map('maps/hard.txt')
board.print_board(boxes, player)

path = Astar_search(board, boxes, player)
for boxes, player in path[::-1]:
    board.print_board(boxes, player)

# from board import Position
# boxes = set([Position(2, 6), Position(2, 4), Position(4, 3)])
# board.
