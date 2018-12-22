import time
from pymouse import PyMouse

m = PyMouse()


def focus(x, y):
    m.press(x, y)
    time.sleep(1)
    m.release(x, y)
    time.sleep(1)


def move_mouse(path):
    x, y = path.pop(0)
    m.press(x, y)
    time.sleep(0.2)
    for px, py in path:
        m.move(px, py)
        time.sleep(0.2)
    m.release(*path[-1])
    time.sleep(0.2)
