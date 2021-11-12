from __future__ import annotations

from math import ceil

num_to_braille = [
    [" ", "⢀", "⢠", "⢰", "⢸"],
    ["⡀", "⣀", "⣠", "⣰", "⣸"],
    ["⡄", "⣄", "⣤", "⣴", "⣼"],
    ["⡆", "⣆", "⣦", "⣶", "⣾"],
    ["⡇", "⣇", "⣧", "⣷", "⣿"],
]

num_to_braille_upside_down = [
    [" ", "⠈", "⠘", "⠸", "⢸"],
    ["⠁", "⠉", "⠙", "⠹", "⢹"],
    ["⠃", "⠋", "⠛", "⠻", "⢻"],
    ["⠇", "⠏", "⠟", "⠿", "⢿"],
    ["⡇", "⡏", "⡟", "⡿", "⣿"],
]


class BrailleStream:
    def __init__(
        self,
        width: int,
        height: int,
        minval: float,
        maxval: float,
        flipud: bool = False,
    ):
        # Store two alternating sets of graphs. This is necessary because
        # Braille symbols fit two values in each character.
        self._graphs = [
            [" " * width] * height,
            [" " * width] * height,
        ]
        self.graph_0_is_active = True
        self.width = width
        self.height = height
        self.minval = minval
        self.maxval = maxval
        self._last_blocks = [0] * height
        # store all values for resize purposes
        self.values: list[float] = [minval]
        self.flipud = flipud
        self.lookup = num_to_braille_upside_down if flipud else num_to_braille

    def value_to_blocks(self, value: float):
        # value -> number of dots
        if value < self.minval:
            k = 0
        elif value > self.maxval:
            k = 4 * self.height
        else:
            k = ceil(
                (value - self.minval) / (self.maxval - self.minval) * 4 * self.height
            )
        # form blocks of 4
        blocks = [4] * (k // 4)
        if k % 4 > 0:
            blocks += [k % 4]
        blocks += [0] * (self.height - len(blocks))
        return blocks

    def add_value(self, value: float):
        blocks = self.value_to_blocks(value)

        chars = [self.lookup[i0][i1] for i0, i1 in zip(self._last_blocks, blocks)]
        if not self.flipud:
            chars = chars[::-1]

        # alternate between graphs[0] and graphs[1]
        self.graph_0_is_active = not self.graph_0_is_active
        g = self._graphs[0 if self.graph_0_is_active else 1]

        # update stream
        for k, char in enumerate(chars):
            g[k] = g[k][1:] + char

        self.values.append(value)
        self._last_blocks = blocks

    @property
    def graph(self):
        return self._graphs[0 if self.graph_0_is_active else 1]

    def resize(self, width: int, height: int):
        return
