from math import ceil

num_to_braille = [
    [" ", "⢀", "⢠", "⢰", "⢸"],
    ["⡀", "⣀", "⣠", "⣰", "⣸"],
    ["⡄", "⣄", "⣤", "⣴", "⣼"],
    ["⡆", "⣆", "⣦", "⣶", "⣾"],
    ["⡇", "⣇", "⣧", "⣷", "⣿"],
]

class BrailleStream:
    def __init__(self, num_chars: int, minval: float, maxval: float):
        self._graphs = [" " * num_chars, " " * num_chars]
        self.minval = minval
        self.maxval = maxval
        self._last_k = 0
        self.last_value: float = minval

    def add_value(self, value):
        k = ceil((value - self.minval) / (self.maxval - self.minval) * 4)
        char = num_to_braille[self._last_k][k]

        # roll list
        self._graphs.append(self._graphs.pop(0))
        # update stream
        self._graphs[0] = self._graphs[0][1:] + char

        self.last_value = value
        self._last_k = k

    @property
    def graph(self):
        return self._graphs[0]
