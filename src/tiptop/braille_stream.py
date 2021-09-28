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
        self._graphs = [
            [" " * width] * height,
            [" " * width] * height,
        ]
        self.height = height
        self.minval = minval
        self.maxval = maxval
        self._last_blocks = [0] * height
        self.last_value: float = minval
        self.flipud = flipud

    def add_value(self, value: float):
        if value < self.minval:
            k = 0
        elif value > self.maxval:
            k = 4 * self.height
        else:
            k = ceil(
                (value - self.minval) / (self.maxval - self.minval) * 4 * self.height
            )

        blocks = [4] * (k // 4)
        if k % 4 > 0:
            blocks += [k % 4]
        blocks += [0] * (self.height - len(blocks))

        dictionary = num_to_braille_upside_down if self.flipud else num_to_braille

        chars = [dictionary[i0][i1] for i0, i1 in zip(self._last_blocks, blocks)]
        if not self.flipud:
            chars = chars[::-1]

        # alternate between graphs[0] and graphs[1]
        self._graphs.append(self._graphs.pop(0))

        # update stream
        for k, char in enumerate(chars):
            self._graphs[0][k] = self._graphs[0][k][1:] + char

        self.last_value = value
        self._last_blocks = blocks

    @property
    def graph(self):
        return self._graphs[0]
