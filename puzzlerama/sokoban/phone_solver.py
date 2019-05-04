import cv2
import subprocess
import numpy as np
from PIL import Image

from board import Position, Board
from algorithms.Astar import Astar_search

LENGTH = 86


def image_save(i):
    img = get_image()[300:-300]
    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    file_index = str(i)
    file_index = (3 - len(file_index)) * '0' + file_index
    image.save(f'images/out_{file_index}.png')


def get_image():
    command = "adb shell screencap -p"
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    out = proc.stdout.read()
    img = cv2.imdecode(np.frombuffer(out, np.uint8), cv2.IMREAD_COLOR)
    img = img[300:-200]
    return img


def get_squares(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # threshold image
    ret, threshed_img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    # find contours and get the external one
    _, contours, hier = cv2.findContours(threshed_img, cv2.RETR_TREE,
                                         cv2.CHAIN_APPROX_SIMPLE)

    max_area = 0
    max_rect = None
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h > max_area:
            max_area = w * h
            max_rect = (x, y, w, h)

    x_0, y_0, w, h = max_rect
    m1, m2 = round(w / LENGTH), round(h / LENGTH)
    squares = [[None for _ in range(m1)] for _ in range(m2)]
    for i in np.arange(m1):
        x = i * LENGTH + x_0
        for j in np.arange(m2):
            y = j * LENGTH + y_0
            squares[j][i] = img[y:y + LENGTH, x:x + LENGTH]

    return squares


def detect(square):
    if np.abs(square.mean(axis=(0, 1)) - np.array([159, 225, 254])).sum() < 24:
        return "#"
    circles = cv2.HoughCircles(
        square[:, :, 2], cv2.HOUGH_GRADIENT, 1, 50, param1=80, param2=30)
    if circles is not None:
        if len(circles[0]) == 1:
            radius = circles[0][0][2]
            if abs(radius - 22) < 2:
                return '.'
            elif abs(radius - 37) < 2:
                return '@'
            else:
                raise Exception('Detect a strange circle!')
        elif len(circles[0]) > 1:
            raise Exception('Detect two circle!')

    if (square.mean(axis=(0, 1)) > 200).all():
        return '$'

    if np.abs(square.mean(axis=(0, 1)) - np.array([195, 135, 235])).sum() < 24:
        return "*"

    # edges = cv2.Canny(square[:, :, 1], 25, 54)
    # lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
    # if lines is not None:
    #     if len(lines[0]) == 1:
    #         if abs(lines[0][0][1] - 2.356) > 0.05:
    #             raise Exception('Detect a strange line!')
    #         return '*'
    #     elif len(lines[0]) > 1:
    #         raise Exception('Detect two lines!')

    return ' '


WALL = set(['#'])
PLAYER = set(['@', '+'])
GOAL = set(['.', '+', '*'])
BOX = set(['$', '*'])


def main():
    img = get_image()
    squares = get_squares(img)

    walls, goals = set(), set()
    boxes, player = set(), None

    num_lines = len(squares)

    for y, line in enumerate(squares):
        for x, s in enumerate(line):
            char = detect(s)
            pos = Position(x, y)

            if char in WALL:
                walls.add(pos)
            if char in GOAL:
                goals.add(pos)
            if char in BOX:
                boxes.add(pos)
            if char in PLAYER:
                player = pos

    board = Board(num_lines, walls, goals)
    board.print_board(boxes, player)

    path = Astar_search(board, boxes, player)
    idx = 0
    for boxes, player in path[::-1]:
        idx += 1
        subprocess.call('clear')
        board.print_board(boxes, player)
        input()
        # image_save(idx)


if __name__ == '__main__':
    main()
