import cv2
import subprocess
import numpy as np
import pyscreenshot as ImageGrab

from screen import get_board

from solver_v3 import Board as BoardV3
from solver_v4 import Board as BoardV4

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

# board = ['ttST', 't330', 'tS3t', 'd3Ts', 'd23D', 'dDss']
with StopWatch():
    print('solver v4')
    BoardV4(board).solve()
with StopWatch():
    print('solver v3')
    BoardV3(board).solve()
