from collections import defaultdict


class StateSet:
    def __init__(self):
        self.cache = defaultdict(dict)

    def __contains__(self, item):
        boxes, player = item
        if boxes in self.cache:
            state_info = self.cache[boxes]
            for norm_pos in state_info:
                if player in state_info[norm_pos]:
                    return True
        return False

    def update(self, boxes, norm_pos, reachable):
        self.cache[boxes][norm_pos] = reachable

    def look_up(self, item):
        boxes, player = item
        if boxes in self.cache:
            state_info = self.cache[boxes]
            for norm_pos in state_info:
                if player in state_info[norm_pos]:
                    return norm_pos
        return None
