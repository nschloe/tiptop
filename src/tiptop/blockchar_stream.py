from math import ceil

num_to_blockchar = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


class BlockCharStream:
    def __init__(self, width: int, height: int, minval: float, maxval: float):
        self.graph = [" " * width] * height
        self.height = height
        self.minval = minval
        self.maxval = maxval
        self.last_value: float = minval

    def add_value(self, value):
        k = ceil((value - self.minval) / (self.maxval - self.minval) * 8 * self.height)

        blocks = [8] * (k // 8)
        if k % 8 > 0:
            blocks += [k % 8]
        blocks += [0] * (self.height - len(blocks))

        chars = [num_to_blockchar[i] for i in blocks]

        # update stream
        for k, char in enumerate(chars[::-1]):
            self.graph[k] = self.graph[k][1:] + char

        self.last_value = value
