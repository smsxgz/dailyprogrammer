# https://blog.csdn.net/yzf0011/article/details/60574388

from math import log2
from .stateset import StateSet


class FibonacciNode:
    def __init__(self, value):
        self.value = value
        self.degree = 0

        self.left = self
        self.right = self

        self.parent = None
        self.child = None

        self.marked = False

    def __gt__(self, n2):
        return self.value['fscore'] > n2.value['fscore']

    def __ge__(self, n2):
        return self.value['fscore'] >= n2.value['fscore']

    @property
    def _key(self):
        return (self.value['boxes'], self.value['norm_pos'])

    def __repr__(self):
        return f"Node({self.value['fscore']})"


class FibonacciHeap:
    def __init__(self, node=None):
        self.cache = dict()
        self.state_set = StateSet()

        if node:
            self.num_key = 1
            self.min_node = node
            self.cache[node._key] = node

        else:
            self.num_key = 0
            self.min_node = None

    @property
    def is_empty(self):
        return self.num_key == 0

    def look_up(self, item):
        return self.state_set.look_up(item)

    def get_gscore(self, key):
        return self.cache[key].value['gscore']

    def merge(self, h2):
        self.num_key += h2.num_key

        if self.min_node is None:
            self.min_node = h2.min_node

        elif h2.min_node:
            min_h1 = self.min_node
            min_right_h1 = min_h1.right
            min_h2 = h2.min_node
            min_right_h2 = min_h2.right

            min_h1.right = min_right_h2
            min_right_h2.left = min_h1

            min_h2.right = min_right_h1
            min_right_h1.left = min_h2

            if self.min_node > h2.min_node:
                self.min_node = h2.min_node

    def add(self, boxes, norm_pos, reachable, moves, gscore, fscore):
        # print(f'Add {(boxes, norm_pos)}')
        value = {
            'boxes': boxes,
            'norm_pos': norm_pos,
            'reachable': reachable,
            'moves': moves,
            'gscore': gscore,
            'fscore': fscore
        }

        self.state_set.update(boxes, norm_pos, reachable)

        node = FibonacciNode(value)
        self.cache[node._key] = node

        h = FibonacciHeap(node)
        self.merge(h)

    def pop(self):
        z = self.min_node
        if z is None:
            return

        self.num_key -= 1

        firstChid = z.child
        if firstChid:
            sibling = firstChid.right
            min_right = z.right

            z.right = firstChid
            firstChid.left = z
            min_right.left = firstChid
            firstChid.right = min_right

            firstChid.parent = None
            min_right = firstChid
            while firstChid is not sibling:
                sibling_right = sibling.right

                z.right = sibling
                sibling.left = z
                sibling.right = min_right
                min_right.left = sibling

                min_right = sibling
                sibling = sibling_right

                sibling.parent = None

        z.left.right = z.right
        z.right.left = z.left

        if z is z.right:
            self.min_node = None
        else:
            self.min_node = z.right
            self.consolidate()

        value = z.value
        self.cache.pop(z._key)
        # print(f'Pop {z._key}')
        return value

    @staticmethod
    def link(y, x):
        """Link node y to x. """
        y.left.right = y.right
        y.right.left = y.left

        child = x.child
        if child is None:
            x.child = y
            y.left = y
            y.right = y
        else:
            y.right = child.right
            child.right.left = y
            y.left = child
            child.right = y
        y.parent = x
        x.degree += 1
        y.marked = False

    def consolidate(self):
        dn = int(log2(self.num_key)) + 2
        A = [None for i in range(dn)]

        w = self.min_node
        f = w.left

        while w is not f:
            d = w.degree
            x = w
            w = w.right
            while A[d] is not None:
                y = A[d]
                if x > y:
                    x, y = y, x
                self.link(y, x)
                A[d] = None
                d += 1

            A[d] = x

        d = w.degree
        x = w
        w = w.right

        while A[d]:
            y = A[d]
            if x > y:
                x, y = y, x
            self.link(y, x)
            A[d] = None
            d += 1

        A[d] = x

        min_key = None
        for i in range(dn):
            if A[i] and (min_key is None or min_key > A[i]):
                self.min_node = A[i]
                min_key = A[i]

    def decreaseKey(self, key, gscore):
        x = self.cache[key]

        if gscore >= x.value['gscore']:
            return

        x.value['fscore'] += (gscore - x.value['gscore'])
        x.value['gscore'] = gscore

        y = x.parent
        if y and y > x:
            self.cut(x, y)
            self.cascadingCut(y)

        if self.min_node > x:
            self.min_node = x

    def cut(self, x, y):
        if y.degree == 1:
            y.child = None
        else:
            x.left.right = x.right
            x.right.left = x.left

            y.child = x.right

        x.left = self.min_node
        x.right = self.min_node.right
        self.min_node.right = x
        x.right.left = x

        x.parent = None
        x.marked = False
        y.degree -= 1

    def cascadingCut(self, y):
        z = y.parent
        if z:
            if not y.marked:
                y.marked = True
            else:
                self.cut(y, z)
                self.cascadingCut(z)


if __name__ == '__main__':
    import random
    h = FibonacciHeap()
    for i in range(10):
        g = random.randint(1, 100)
        print(g)
        h.add(i, i, None, None, g, g + 10)

    for i in range(10):
        print(len(h.cache), h.num_key)
        print(h.pop())
