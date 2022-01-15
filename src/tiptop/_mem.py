import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from ._helpers import sizeof_fmt
from .braille_stream import BrailleStream


class Mem(Widget):
    def on_mount(self):
        self.is_first_render = True

        self.mem_total_bytes = psutil.virtual_memory().total
        self.mem_total_string = sizeof_fmt(self.mem_total_bytes, fmt=".2f")

        # check which mem sections are available on the machine
        self.attrs = []
        mem = psutil.virtual_memory()
        self.colors = ["yellow", "green", "blue", "magenta"]
        for attr in ["free", "available", "cached", "used"]:
            if hasattr(mem, attr):
                self.attrs.append(attr)

        # append spaces to make all names equally long
        maxlen = max(len(string) for string in self.attrs)
        maxlen = min(maxlen, 5)
        self.labels = [attr[:maxlen].ljust(maxlen) for attr in self.attrs]

        # can't use
        # [BrailleStream(40, 4, 0.0, self.mem_total_bytes)] * len(self.names)
        # since that only creates one BrailleStream, references n times.
        self.mem_streams = []
        for _ in range(len(self.attrs)):
            self.mem_streams.append(BrailleStream(40, 4, 0.0, self.mem_total_bytes))

        self.set_interval(2.0, self.collect_data)

    def collect_data(self):
        mem = psutil.virtual_memory()
        graphs = []
        for attr, label, stream in zip(self.attrs, self.labels, self.mem_streams):
            val = getattr(mem, attr)
            stream.add_value(val)
            val_string = " ".join(
                [
                    label,
                    sizeof_fmt(val, fmt=".2f"),
                    f"({val / self.mem_total_bytes * 100:.0f}%)",
                ]
            )
            graphs.append(
                "\n".join(
                    [val_string + stream.graph[0][len(val_string) :]] + stream.graph[1:]
                )
            )

        table = Table(box=None, expand=True, padding=0, show_header=False)
        table.add_column(justify="left", no_wrap=True)
        for k, graph in enumerate(graphs):
            table.add_row(f"[{self.colors[k]}]{graph}[/]")

        self.panel = Panel(
            table,
            title=f"mem - {self.mem_total_string}",
            title_align="left",
            border_style="green",
            box=box.SQUARE,
        )
        self.refresh()

    def render(self) -> Panel:
        if self.is_first_render:
            self.collect_data()
            self.is_first_render = False
        return self.panel

    async def on_resize(self, event):
        for ms in self.mem_streams:
            ms.reset_width(event.width - 4)

        # split the available event.height-2 into n even blocks, and if there's
        # a rest, divide it up into the last, e.g., with n=4
        # 17 -> 4, 4, 4, 5
        n = len(self.attrs)
        heights = [(event.height - 2) // n] * n
        for k in range((event.height - 2) % n):
            heights[-(k + 1)] += 1

        for ms, h in zip(self.mem_streams, heights):
            ms.reset_height(h)
