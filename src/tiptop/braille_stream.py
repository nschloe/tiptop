from __future__ import annotations

from math import ceil

# String lookup and list lookup are equally fast, see
# <https://gist.github.com/nschloe/d790a873081dc504193c99d3758755b4>
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


def _transpose(l):
    # https://stackoverflow.com/a/6473724/353337
    return map(list, zip(*l))


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
        # we store one more value than what is displayed to account for the "old" graph
        self.values: list[float] = [minval] * (2 * self.width + 1)
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

        self.values = self.values[1:] + [value]
        self._last_blocks = blocks

    @property
    def graph(self):
        return self._graphs[0 if self.graph_0_is_active else 1]

    def reset_width(self, width: int):
        if width == self.width:
            return
        elif width > self.width:
            diff = width - self.width
            self._graphs = [[" " * diff + row for row in g] for g in self._graphs]
            self.values = [self.minval] * (2 * diff) + self.values
        elif width < self.width:
            self._graphs = [[row[-width:] for row in g] for g in self._graphs]
            self.values = self.values[-(2 * width + 1) :]

        self.width = width

    def reset_height(self, height: int):
        if height == self.height:
            return

        # recreate both _graphs
        self.height = height
        blocks = [self.value_to_blocks(value) for value in self.values]

        assert len(self.values) == 2 * self.width + 1
        g = [
            # 0 -> 2 * k + 1
            [
                [
                    self.lookup[i0][i1]
                    for i0, i1 in zip(blocks[2 * k], blocks[2 * k + 1])
                ]
                for k in range(self.width)
            ],
            # 1 -> 2 * k + 2
            [
                [
                    self.lookup[i0][i1]
                    for i0, i1 in zip(blocks[2 * k + 1], blocks[2 * k + 2])
                ]
                for k in range(self.width)
            ],
        ]
        if not self.flipud:
            g = [
                [row[::-1] for row in g[0]],
                [row[::-1] for row in g[1]],
            ]
        # transpose and join
        self._graphs = [
            ["".join(row) for row in _transpose(g[0])],
            ["".join(row) for row in _transpose(g[1])],
        ]
        if self.graph_0_is_active:
            self._graphs = [self._graphs[1], self._graphs[0]]

        self._last_blocks = blocks[-1]
