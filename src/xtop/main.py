import os
import socket
import time
from datetime import datetime, timedelta
from math import ceil
import itertools

import psutil
from rich import align, box
from rich.panel import Panel
from rich.table import Table
from textual.app import App
from textual.widget import Widget


def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)


def values_to_braille(values, minval: float, maxval: float) -> str:
    assert len(values) % 2 == 0, len(values)
    k = [ceil((val - minval) / (maxval - minval) * 4) for val in values]
    # iterate over pairs
    d = {
        (0, 0): " ",
        (0, 1): "⢀",
        (0, 2): "⢠",
        (0, 3): "⢰",
        (0, 4): "⢸",
        #
        (1, 0): "⡀",
        (1, 1): "⣀",
        (1, 2): "⣠",
        (1, 3): "⣰",
        (1, 4): "⣸",
        #
        (2, 0): "⡄",
        (2, 1): "⣄",
        (2, 2): "⣤",
        (2, 3): "⣴",
        (2, 4): "⣼",
        #
        (3, 0): "⡆",
        (3, 1): "⣆",
        (3, 2): "⣦",
        (3, 3): "⣶",
        (3, 4): "⣾",
        #
        (4, 0): "⡇",
        (4, 1): "⣇",
        (4, 2): "⣧",
        (4, 3): "⣷",
        (4, 4): "⣿",
    }
    chars = [d[pair] for pair in zip(k[0::2], k[1::2])]
    return "".join(chars)


def val_to_color(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = int(round(t * 3))
    return {0: "color(4)", 1: "color(6)", 2: "color(6)", 3: "color(2)"}[k]


class InfoLine(Widget):
    def render(self):
        now = datetime.now().strftime("%c")
        uptime_s = time.time() - psutil.boot_time()
        d = datetime(1, 1, 1) + timedelta(seconds=uptime_s)

        battery = psutil.sensors_battery().percent
        return align.Align(
            "[color(8)]"
            + f"{now}, "
            + f"up {d.day - 1} days, {d.hour}:{d.minute}, "
            + f"BAT {round(battery)}%"
            + "[/]",
            "center",
        )

    def on_mount(self):
        self.set_interval(2.0, self.refresh)


class CPU(Widget):
    def on_mount(self):
        self.data = []
        self.num_cores = psutil.cpu_count(logical=False)
        self.num_threads = psutil.cpu_count(logical=True)
        self.cpu_percent_data = [0.0] * 20
        self.cpu_percent_indiv = [[0.0] * 20 for _ in range(self.num_threads)]
        self.temp_low = 30.0
        self.temp_high = psutil.sensors_temperatures()["coretemp"][0].high
        self.temp_total = [self.temp_low] * 10

        self.collect_data()
        self.set_interval(2.0, self.collect_data)

    def collect_data(self):
        self.temp_total.pop(0)
        self.temp_total.append(psutil.sensors_temperatures()["coretemp"][0].current)
        self.total_temp_graph = values_to_braille(
            self.temp_total, self.temp_low, self.temp_high
        )

        self.cpu_percent_data.pop(0)
        self.cpu_percent_data.append(psutil.cpu_percent())
        self.cpu_percent_graph = values_to_braille(self.cpu_percent_data, 0.0, 100.0)
        self.color_total = val_to_color(self.cpu_percent_data[-1], 0.0, 100.0)

        load_indiv = psutil.cpu_percent(percpu=True)
        self.colors = []
        self.graphs = []
        for k in range(self.num_threads):
            self.cpu_percent_indiv[k].pop(0)
            self.cpu_percent_indiv[k].append(load_indiv[k])
            self.graphs.append(values_to_braille(self.cpu_percent_indiv[k], 0.0, 100.0))
            self.colors.append(val_to_color(load_indiv[k], 0.0, 100.0))

        # textual method
        self.refresh()

    def render(self):
        percent = int(round(self.cpu_percent_data[-1]))
        lines = [
            f"[b]CPU[/] [{self.color_total}]{self.cpu_percent_graph} {percent:3d}%[/]  "
            f"[color(5)]{self.total_temp_graph} {int(self.temp_total[-1])}°C[/]"
        ]

        lines += [
            f"[b]P{k + 1:<2d}[/] [{color}]{graph} {int(round(data[-1])):3d}%[/]"
            for k, (data, graph, color) in enumerate(
                zip(self.cpu_percent_indiv, self.graphs, self.colors)
            )
        ]

        title = f"{self.num_cores} cores, {self.num_threads} threads, {int(psutil.cpu_freq().current)} MHz"

        load_avg = os.getloadavg()
        subtitle = f"Load Avg:   {load_avg[0]:.2f}  {load_avg[1]:.2f}  {load_avg[2]:.2f}"

        p = align.Align(
            Panel(
                "\n".join(lines),
                title=title,
                title_align="left",
                subtitle=subtitle,
                border_style="color(8)",
                box=box.SQUARE,
            ),
            "right",
            vertical="middle",
        )
        return Panel(
            p, title=f"cpu", title_align="left", border_style="color(4)", box=box.SQUARE
        )


class Mem(Widget):
    def render(self) -> Panel:
        return Panel(
            "Hello [b]Mem[/b]",
            title="mem",
            title_align="left",
            border_style="color(2)",
            box=box.SQUARE,
        )


class ProcsList(Widget):
    def on_mount(self):
        self.collect_data()
        self.set_interval(2.0, self.collect_data)

    def collect_data(self):
        self.processes = list(psutil.process_iter())
        self.cpu_percent = [p.cpu_percent() for p in self.processes]
        # sort by cpu_percent
        self.idx = argsort(self.cpu_percent)[::-1]
        self.refresh()

    def render(self) -> Panel:
        table = Table(show_header=True, header_style="bold", box=box.MINIMAL)
        table.add_column("pid", width=8, no_wrap=True)
        table.add_column("program", style="color(2)", width=12, no_wrap=True)
        table.add_column("args", width=12, no_wrap=True)
        table.add_column("cpu%", style="color(2)", width=12, no_wrap=True)

        table.padding = 0
        table.border_style = "none"
        for i in self.idx[:20]:
            table.add_row(
                str(self.processes[i].pid),
                self.processes[i].name(),
                " ".join(self.processes[i].cmdline()),
                f"{self.cpu_percent[i]:.1f}",
            )

        return Panel(
            table,
            title="proc",
            title_align="left",
            border_style="color(6)",
            box=box.SQUARE,
        )


class Net(Widget):
    def render(self) -> Panel:
        ip = socket.gethostbyname(socket.gethostname())
        return Panel(
            "Hello [b]Net[/b]",
            title=f"net - {ip}",
            title_align="left",
            border_style="color(1)",
            box=box.SQUARE,
        )


class Xtop(App):
    async def on_mount(self) -> None:
        await self.view.dock(InfoLine(), edge="top", size=1, name="info")
        await self.view.dock(CPU(), edge="top", size=15, name="cpu")
        await self.view.dock(ProcsList(), edge="right", size=50, name="proc")
        await self.view.dock(Mem(), edge="top", size=20, name="mem")
        await self.view.dock(Net(), edge="bottom", name="net")

    async def on_load(self, _):
        await self.bind("i", "view.toggle('info')", "Toggle info")
        await self.bind("c", "view.toggle('cpu')", "Toggle cpu")
        await self.bind("m", "view.toggle('mem')", "Toggle mem")
        await self.bind("n", "view.toggle('net')", "Toggle net")
        await self.bind("p", "view.toggle('proc')", "Toggle proc")
        await self.bind("q", "quit", "quit")


Xtop.run()
