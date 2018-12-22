import cv2
import numpy as np

from PIL import Image


def image_show(img):
    if len(img.shape) == 2:
        img = np.tile(np.expand_dims(img, -1), (1, 1, 3))
    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    image.show()


def is_diamond(approx):
    mem = []
    for p in approx:
        x = p[0][0]
        flag = True
        for m in mem:
            if abs(x - m) < 5:
                flag = False
        if flag:
            mem.append(x)
    if len(mem) == 2:
        return False
    elif len(mem) == 3:
        return True
    else:
        raise Exception('Something Wrong!')


def find_levels(xs):
    levels = []
    while len(xs) > 0:
        min_x = min(xs)
        tmp = []
        tmp_xs = []
        for x in xs:
            if abs(x - min_x) < 10:
                tmp.append(x)
            else:
                tmp_xs.append(x)

        xs = tmp_xs
        levels.append(sum(tmp) // len(tmp))
    return levels


def get_board(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary1 = cv2.threshold(gray, 150, 1, cv2.THRESH_BINARY)
    # _, binary2 = cv2.threshold(gray, 0, 1,
    #                            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, binary2 = cv2.threshold(gray, 180, 1, cv2.THRESH_BINARY_INV)
    _, binary3 = cv2.threshold(gray, 230, 1, cv2.THRESH_BINARY)
    binary = (
        1 - (np.logical_and(binary1, binary2).astype('uint8') + binary3)) * 255
    # image_show(binary)

    out_binary, contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE,
                                                       cv2.CHAIN_APPROX_SIMPLE)

    # result = img.copy()
    shapes = []
    idx = 0
    while True:
        mm = cv2.moments(contours[idx])
        cx = int(mm['m10'] / mm['m00'])
        cy = int(mm['m01'] / mm['m00'])
        # cv2.circle(result, (cx, cy), 3, (0, 0, 255), -1)

        info = {}
        info['centroid'] = (cx, cy)

        epsilon = 0.01 * cv2.arcLength(contours[idx], True)
        approx = cv2.approxPolyDP(contours[idx], epsilon, True)

        info['vertex'] = approx
        if len(approx) == 3:
            info['shape'] = 'triangle'
            is_endpoints = False
            if hierarchy[0][idx][2] != -1:
                is_endpoints = True
            info['end_points'] = is_endpoints

        elif len(approx) == 4:
            if is_diamond(approx):
                info['shape'] = 'diamond'
            else:
                info['shape'] = 'square'
            is_endpoints = False
            if hierarchy[0][idx][2] != -1:
                is_endpoints = True
            info['end_points'] = is_endpoints

        elif len(approx) == 8:
            info['shape'] = 'octagon'
            visits = 0
            tmp = hierarchy[0][idx][2]
            while True:
                visits += 1
                tmp = hierarchy[0][tmp][0]
                if tmp == -1:
                    break
            info['visits'] = visits

        else:
            # result = img.copy()
            # cv2.drawContours(result, contours, idx, (0, 255, 0), 2)
            # image_show(result)
            # raise Exception('Something Wrong!')
            continue

        # cv2.drawContours(result, contours, idx, (0, 255, 0), 2)
        shapes.append(info)

        idx = hierarchy[0][idx][0]
        if idx == -1:
            break
    # image_show(result)

    ys, xs = zip(*[s['centroid'] for s in shapes])
    x_levels = find_levels(xs)
    y_levels = find_levels(ys)

    row = len(x_levels)
    col = len(y_levels)

    x_interval = (x_levels[-1] - x_levels[0]) / (row - 1)
    y_interval = (y_levels[-1] - y_levels[0]) / (col - 1)
    assert abs(x_interval - y_interval) < 5

    board = [['0' for _ in range(col)] for _ in range(row)]
    for info in shapes:
        cy, cx = info['centroid']
        i = round((cx - x_levels[0]) / x_interval)
        j = round((cy - y_levels[0]) / y_interval)
        if info['shape'] in ['square', 'triangle', 'diamond']:
            board[i][j] = info['shape'][0]
            if info['end_points']:
                board[i][j] = board[i][j].upper()
        else:
            board[i][j] = str(info['visits'])
    return board, (x_levels[0], x_interval), (y_levels[0], y_interval)


if __name__ == '__main__':
    import subprocess
    import pyscreenshot as ImageGrab

    from solver import Board

    print("Please click on the window of the game LYNE.")
    res = subprocess.getoutput('xwininfo')
    num = [int(s) for s in res.split() if s.isdigit()]

    while True:
        input("Press enter for starting.")
        img = ImageGrab.grab(
            bbox=(num[0], num[1], num[0] + num[4], num[1] + num[5]))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        board = get_board(img)[0]
        from IPython import embed
        embed()
        board = Board(board)
        paths = board.solve()
        for path in paths:
            board._print_path(path)
