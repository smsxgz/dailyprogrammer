# https://www.reddit.com/r/dailyprogrammer/comments/aqwvxo/20190215_challenge_375_hard_graph_of_thrones/

from collections import defaultdict
from mylib import StopWatch


def solve():
    N, M = input().strip().split(' ')
    N, M = int(N), int(M)
    assert N * (N - 1) == 2 * M

    graph = defaultdict(set)
    edges = 0
    for _ in range(M):
        msg = input().strip()
        if '++' in msg:
            n1, n2 = msg.split(" ++ ")
            graph[n1].add(n2)
            graph[n2].add(n1)
            edges += 1
    if edges == M:
        return True

    # The graph is balanced iff every component of the positive subgraph
    # is complete, and there are at most 2 of them.
    n = list(graph.keys())[0]
    nodes1 = graph[n].copy()
    nodes1.add(n)
    nodes2 = set(graph.keys()) - nodes1
    for n in graph:
        if n in nodes1:
            if len(graph[n] & nodes1) == len(nodes1) - 1 and len(
                    graph[n] & nodes2) == 0:
                continue
            else:
                return False
        else:
            if len(graph[n] & nodes2) == len(nodes2) - 1 and len(
                    graph[n] & nodes1) == 0:
                continue
            else:
                return False
    return True


def solve2():
    """from /u/brickses"""
    NO_GROUP, GROUP_0, GROUP_1 = 0, 1, 2
    N, M = [int(x) for x in input().split(' ')]
    assert N * (N - 1) == 2 * M
    groups = [set([]), set([])]

    for _ in range(M):
        line = input().strip()

        # Relationship type
        if '++' in line:
            friend = True
            split = ' ++ '
        else:
            friend = False
            split = ' -- '
        people = line.split(split)

        # Grouping of person 0
        pg0 = NO_GROUP
        if people[0] in groups[0]:
            pg0 = GROUP_0
        if people[0] in groups[1]:
            pg0 = GROUP_1

        # Grouping of person 1
        pg1 = NO_GROUP
        if people[1] in groups[0]:
            pg1 = GROUP_0
        if people[1] in groups[1]:
            pg1 = GROUP_1

        if (pg1 and pg0):  # Both poeple assigned to teams
            if (pg1 == pg0) != friend:
                return "Unbalanced Graph"
        elif pg1:  # Person 1 on a team
            groups[pg1 - 1 == friend].add(people[0])
        elif pg0:  # Person 0 on a team
            groups[pg0 - 1 == friend].add(people[1])
        else:  # Neither person on a team.
            groups[0].add(people[0])
            groups[not friend].add(people[1])

    return "Balanced Graph"


if __name__ == '__main__':
    with StopWatch():
        print(solve())
    with StopWatch():
        print(solve2())
