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

        self.mem_streams = [
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
        ]
        self.set_interval(2.0, self.collect_data)

    def collect_data(self):
        mem = psutil.virtual_memory()
        names = ["used  ", "avail ", "cached", "free  "]
        values = [mem.used, mem.available, mem.cached, mem.free]
        graphs = []
        for name, stream, val in zip(names, self.mem_streams, values):
            stream.add_value(val)
            val_string = " ".join(
                [
                    name,
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
        table.add_row("[color(2)]" + graphs[0] + "[/]")
        table.add_row("[color(3)]" + graphs[1] + "[/]")
        table.add_row("[color(4)]" + graphs[2] + "[/]")
        table.add_row("[color(5)]" + graphs[3] + "[/]")

        self.panel = Panel(
            table,
            title=f"mem - {self.mem_total_string}",
            title_align="left",
            border_style="color(2)",
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

        # split the available event.height-2 into 4 even blocks, and if there's
        # a rest, divide it up into the first, e.g.,
        # 17 -> 5, 4, 4, 4
        heights = [(event.height - 2) // 4] * 4
        for k in range((event.height - 2) % 4):
            heights[k] += 1

        for ms, h in zip(self.mem_streams, heights):
            ms.reset_height(h)
