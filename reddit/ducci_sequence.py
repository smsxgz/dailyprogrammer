# https://www.reddit.com/r/dailyprogrammer/comments/8sjcl0/20180620_challenge_364_intermediate_the_ducci/


def ducci_sequence(ns):
    while True:
        yield ns
        ns = tuple(abs(ns[i - 1] - ns[i]) for i in range(len(ns)))


def ducci(ns):
    known = set()
    for ns in ducci_sequence(ns):
        if ns in known or set(ns) == {0}:
            break
        known.add(ns)
    return len(known) + 1


def ducci1(seq):
    steps, seq_dict = 1, {}

    while sum(seq) != 0 and tuple(seq) not in seq_dict:
        seq_dict[tuple(seq)], steps, seq = 1, steps + 1, [
            abs(seq[pos] - seq[pos + 1]) for pos in range(-1,
                                                          len(seq) - 1)
        ]
    return steps


if __name__ == "__main__":
    import time
    seq = tuple(map(int, input('Enter your sequence >>> ')[1:-1].split(', ')))
    start = time.time()
    print(ducci(seq), "steps")
    print(time.time() - start)

    start = time.time()
    print(ducci1(seq), "steps")
    print(time.time() - start)
