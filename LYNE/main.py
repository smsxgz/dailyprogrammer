import cv2
import time
import subprocess
import numpy as np
import pyscreenshot as ImageGrab

from screen import get_board
from solver_v5 import Board
from click import move_mouse, focus


def get_mouse_path(path, xs, ys, xbase, ybase):
    mouse_path = []
    for px, py in path:
        mouse_path.append((round(xbase + ys[0] + (py - 1) * ys[1]),
                           round(ybase + xs[0] + (px - 1) * xs[1])))
    return mouse_path


def main():
    print("Please click on the window of the game LYNE.")
    res = subprocess.getoutput('xwininfo')
    num = [int(s) for s in res.split() if s.isdigit()]

    # for _ in range(25):
    #     time.sleep(5)
    while True:
        input("Press enter for starting.")
        print('Solving...')
        img = ImageGrab.grab(
            bbox=(num[0], num[1], num[0] + num[4], num[1] + num[5]))
        if img.mode == 'P':
            img = img.convert('RGB')
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

        board, xs, ys = get_board(img)
        print('\n'.join([''.join(t) for t in board]))
        paths = Board(board).solve()

        # Focus on the game window
        focus(num[0] + 100, num[1] + 100)

        for path in paths:
            move_mouse(get_mouse_path(path, xs, ys, num[0], num[1]))


if __name__ == '__main__':
    main()
