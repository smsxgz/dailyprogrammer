import cv2
import subprocess
import numpy as np
import pyscreenshot as ImageGrab

from screen import get_board
from solver_v5 import Board as BoardV5
from solver_v6 import Board as BoardV6

from mylib import StopWatch

print("Please click on the window of the game LYNE.")
res = subprocess.getoutput('xwininfo')
num = [int(s) for s in res.split() if s.isdigit()]

img = ImageGrab.grab(bbox=(num[0], num[1], num[0] + num[4], num[1] + num[5]))
if img.mode == 'P':
    img = img.convert('RGB')
img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

board, xs, ys = get_board(img)
print('\n'.join([''.join(t) for t in board]))

# board = ['ddd', 'd4d', '22d', '23d', '2D2', 'Ddd']
with StopWatch():
    print('solver v5')
    b = BoardV5(board)
    for path in b.solve():
        b._print_path(path)
with StopWatch():
    print('solver v6')
    b = BoardV6(board)
    for path in b.solve():
        b._print_path(path)
