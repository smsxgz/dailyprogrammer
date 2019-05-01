from load_map import load_map
from algorithms.bfs import breadth_first_search
from algorithms.dfs import depth_first_search

board, boxes, player = load_map('maps/advanced.txt')
board.print_board(boxes, player)

# path = breadth_first_search(board, boxes, player)
# for pos, d in path:
#     boxes.remove(pos)
#     boxes.add(pos + d)
#     board.print_board(boxes, pos)

# path = depth_first_search(board, boxes, player)
# for pos, d in path:
#     boxes.remove(pos)
#     boxes.add(pos + d)
#     board.print_board(boxes, pos)
