from datetime import datetime
import os
import socket


import psutil
from rich import align, box
from rich.panel import Panel
from rich.table import Table
from textual.app import App
from textual.widget import Widget


def val_to_braille(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = int(round(t * 3))
    return {0: "⣀", 1: "⣤", 2: "⣶", 3: "⣿"}[k]


def val_to_color(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = int(round(t * 3))
    return {0: "color(4)", 1: "color(6)", 2: "color(6)", 3: "color(2)"}[k]


class InfoLine(Widget):
    def render(self):
        # return Panel(align.Align("hello", "left"), align.Align("x", "right"))
        # return Columns(["x", "B", "CSDSDF"])
        table = Table(border_style=None)
        table.add_column("Released", justify="left", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("Box Office", justify="right", style="green")

        return Panel("B")
        # time = datetime.now().strftime("%c")
        # align.Align(f"[color(8)]{time}[/]", "center")

    def on_mount(self):
        self.set_interval(2.0, self.refresh)


class CPU(Widget):
    def on_mount(self):
        self.data = []
        self.num_cores: int = psutil.cpu_count(logical=False)
        self.num_threads: int = psutil.cpu_count(logical=True)
        self.refresh_rate_s = 2.0
        self.cpu_graph_total = 10 * " "
        self.cpu_graph_indiv = [10 * " "] * 8
        self.cpu_temp_total = 5 * " "
        self.temp_low = 40.0
        self.temp_high = psutil.sensors_temperatures()["coretemp"][0].high

        self.set_interval(self.refresh_rate_s, self.refresh)

    def render(self):
        load_total = psutil.cpu_percent()
        temp_total = psutil.sensors_temperatures()["coretemp"][0].current
        load_indiv = psutil.cpu_percent(percpu=True)
        load_avg = os.getloadavg()

        br = val_to_braille(temp_total, self.temp_low, self.temp_high)
        self.cpu_temp_total = self.cpu_temp_total[1:] + br

        br = val_to_braille(load_total, 0.0, 100.0)
        color_total = val_to_color(load_total, 0.0, 100.0)
        self.cpu_graph_total = self.cpu_graph_total[1:] + br
        colors = []
        for k in range(self.num_threads):
            br = val_to_braille(load_indiv[k], 0.0, 100.0)
            self.cpu_graph_indiv[k] = self.cpu_graph_indiv[k][1:] + br
            colors.append(val_to_color(load_indiv[k], 0.0, 100.0))

        proc_lines = [
            f"[b]P{k + 1:<2d}[/b] [{color}]{graph} {int(round(load)):3d}[/]%"
            for k, (load, graph, color) in enumerate(
                zip(load_indiv, self.cpu_graph_indiv, colors)
            )
        ]

        lines = (
            [
                f"[b]CPU[/b] [{color_total}]{self.cpu_graph_total} {int(round(load_total)):3d}[/]%  "
                f"[color(5)]{self.cpu_temp_total} {int(temp_total)}[/]°C"
            ]
            + proc_lines
            + [f"Load Avg:   {load_avg[0]:.2f}  {load_avg[1]:.2f}  {load_avg[2]:.2f}"]
        )

        p = align.Align(
            Panel(
                "\n".join(lines),
                title=f"{int(psutil.cpu_freq().current)} MHz",
                title_align="left",
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
    def render(self) -> Panel:
        return Panel(
            "Hello [b]ProcsList[/b]",
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


class SimpleApp(App):
    async def on_mount(self) -> None:
        await self.view.dock(InfoLine(), edge="top", size=4)
        await self.view.dock(CPU(), edge="top", size=16, name="cpu")
        await self.view.dock(ProcsList(), edge="right", size=50, name="proc")
        await self.view.dock(Mem(), edge="top", size=20, name="mem")
        await self.view.dock(Net(), edge="bottom", size=20, name="net")

    async def on_load(self, _):
        await self.bind("c", "view.toggle('cpu')", "Toggle cpu")
        await self.bind("m", "view.toggle('mem')", "Toggle mem")
        await self.bind("n", "view.toggle('net')", "Toggle net")
        await self.bind("p", "view.toggle('proc')", "Toggle proc")
        await self.bind("q", "quit")

    # async def action_color(self, color: str) -> None:
    #     self.background = f"on {color}"


SimpleApp.run(log="textual.log")
