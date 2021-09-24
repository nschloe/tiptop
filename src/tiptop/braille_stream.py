from math import ceil

num_to_braille = [
    [" ", "⢀", "⢠", "⢰", "⢸"],
    ["⡀", "⣀", "⣠", "⣰", "⣸"],
    ["⡄", "⣄", "⣤", "⣴", "⣼"],
    ["⡆", "⣆", "⣦", "⣶", "⣾"],
    ["⡇", "⣇", "⣧", "⣷", "⣿"],
]


class BrailleStream:
    def __init__(self, width: int, height: int, minval: float, maxval: float):
        self._graphs = [
            [" " * width] * height,
            [" " * width] * height,
        ]
        self.height = height
        self.minval = minval
        self.maxval = maxval
        self._last_blocks = [0] * height
        self.last_value: float = minval

    def add_value(self, value):
        k = ceil((value - self.minval) / (self.maxval - self.minval) * 4 * self.height)

        blocks = [4] * (k // 4) + [k % 4]
        blocks += [0] * (self.height - len(blocks))

        chars = [num_to_braille[i0][i1] for i0, i1 in zip(self._last_blocks, blocks)]

        # roll list
        self._graphs.append(self._graphs.pop(0))

        # update stream
        for k, char in enumerate(chars[::-1]):
            self._graphs[0][k] = self._graphs[0][k][1:] + char

        self.last_value = value
        self._last_blocks = blocks

    @property
    def graph(self):
        return self._graphs[0]
