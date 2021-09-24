from math import ceil

num_to_blockchar = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


class BlockCharStream:
    def __init__(self, num_chars: int, minval: float, maxval: float):
        self.graph = " " * num_chars
        self.minval = minval
        self.maxval = maxval
        self.last_value: float = minval

    def add_value(self, value):
        k = ceil((value - self.minval) / (self.maxval - self.minval) * 8)
        self.graph = self.graph[1:] + num_to_blockchar[k]
        self.last_value = value
