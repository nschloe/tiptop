from __future__ import annotations

import psutil
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widget import Widget

from ._helpers import sizeof_fmt
from .braille_stream import BrailleStream


class Disk(Widget):
    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.down_box = Panel(
            "",
            title="read",
            title_align="left",
            style="green",
            width=20,
            box=box.SQUARE,
        )
        self.up_box = Panel(
            "",
            title="write",
            title_align="left",
            style="blue",
            width=20,
            box=box.SQUARE,
        )
        self.table = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        self.table.add_column("graph", no_wrap=True, ratio=1)
        self.table.add_column("box", no_wrap=True, width=20)
        self.table.add_row("", self.down_box)
        self.table.add_row("", self.up_box)

        # kick out /dev/loop* devices
        self.mountpoints = [
            item.mountpoint
            for item in psutil.disk_partitions()
            if not item.device.startswith("/dev/loop")
        ]

        self.group = Group(self.table, "")
        self.panel = Panel(
            self.group,
            title="[b]disk[/]",
            # border_style="magenta",
            border_style="white",
            title_align="left",
            box=box.SQUARE,
        )

        self.last_io = None
        self.max_read_bytes_s = 0
        self.max_read_bytes_s_str = ""
        self.max_write_bytes_s = 0
        self.max_write_bytes_s_str = ""

        self.read_stream = BrailleStream(20, 5, 0.0, 1.0e6)
        self.write_stream = BrailleStream(20, 5, 0.0, 1.0e6, flipud=True)

        self.refresh_panel()

        self.interval_s = 2.0
        self.set_interval(self.interval_s, self.refresh_panel)

    def refresh_panel(self):
        io = psutil.disk_io_counters()

        if self.last_io is None:
            read_bytes_s_string = ""
            write_bytes_s_string = ""
        else:
            read_bytes_s = (io.read_bytes - self.last_io.read_bytes) / self.interval_s
            read_bytes_s_string = sizeof_fmt(read_bytes_s, fmt=".1f") + "/s"
            write_bytes_s = (
                io.write_bytes - self.last_io.write_bytes
            ) / self.interval_s
            write_bytes_s_string = sizeof_fmt(write_bytes_s, fmt=".1f") + "/s"

            if read_bytes_s > self.max_read_bytes_s:
                self.max_read_bytes_s = read_bytes_s
                self.max_read_bytes_s_str = sizeof_fmt(read_bytes_s, fmt=".1f") + "/s"

            if write_bytes_s > self.max_write_bytes_s:
                self.max_write_bytes_s = write_bytes_s
                self.max_write_bytes_s_str = sizeof_fmt(write_bytes_s, fmt=".1f") + "/s"

            self.read_stream.add_value(read_bytes_s)
            self.write_stream.add_value(write_bytes_s)

        self.last_io = io

        total_read_string = sizeof_fmt(io.read_bytes, sep=" ", fmt=".1f")
        total_write_string = sizeof_fmt(io.write_bytes, sep=" ", fmt=".1f")

        self.down_box.renderable = "\n".join(
            [
                f"{read_bytes_s_string}",
                f"max   {self.max_read_bytes_s_str}",
                f"total {total_read_string}",
            ]
        )
        self.up_box.renderable = "\n".join(
            [
                f"{write_bytes_s_string}",
                f"max   {self.max_write_bytes_s_str}",
                f"total {total_write_string}",
            ]
        )

        self.table.columns[0]._cells[0] = Text(
            "\n".join(self.read_stream.graph), style="green"
        )
        self.table.columns[0]._cells[1] = Text(
            "\n".join(self.write_stream.graph), style="blue"
        )

        table = Table(box=None, expand=False, padding=(0, 1), show_header=True)
        table.add_column("", justify="left", no_wrap=True, style="bold")
        table.add_column(Text("free", justify="left"), justify="right", no_wrap=True)
        table.add_column(Text("used", justify="left"), justify="right", no_wrap=True)
        table.add_column(Text("total", justify="left"), justify="right", no_wrap=True)
        table.add_column("", justify="right", no_wrap=True)

        for mp in self.mountpoints:
            try:
                du = psutil.disk_usage(mp)
            except PermissionError:
                # https://github.com/nschloe/tiptop/issues/71
                continue

            style = None
            if du.percent > 99:
                style = "red reverse bold"
            elif du.percent > 95:
                style = "yellow"

            table.add_row(
                mp,
                sizeof_fmt(du.free, fmt=".1f"),
                sizeof_fmt(du.used, fmt=".1f"),
                sizeof_fmt(du.total, fmt=".1f"),
                f"({du.percent:.1f}%)",
                style=style,
            )
        self.group.renderables[1] = table

        self.refresh()

    def render(self):
        return self.panel

    async def on_resize(self, event):
        self.read_stream.reset_width(event.width - 25)
        self.write_stream.reset_width(event.width - 25)
