import platform
import socket
import time
from datetime import datetime, timedelta

import cpuinfo
import distro
import psutil

# TODO relative imports
from braille_stream import BrailleStream
from rich import align, box
from rich.panel import Panel
from rich.table import Table
from textual.app import App
from textual.widget import Widget


# https://stackoverflow.com/a/1094933/353337
def sizeof_fmt(num, suffix: str = "iB", sep=" ", fmt=".0f"):
    assert num >= 0
    for unit in ["B", "K", "M", "G", "T", "P", "E", "Z"]:
        # actually 1024, but be economical with the return string size:
        if unit != "B":
            unit += suffix

        if num < 1000:
            string = f"{{:{fmt}}}".format(num)
            return f"{string}{sep}{unit}"
        num /= 1024
    string = f"{{:{fmt}}}".format(num)
    return f"{string}{sep}Y{suffix}"


def val_to_color(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = round(t * 3)
    return {0: "color(4)", 1: "color(6)", 2: "color(6)", 3: "color(2)"}[k]


class InfoLine(Widget):
    def on_mount(self):
        self.set_interval(2.0, self.refresh)
        ri = distro.os_release_info()
        # + f"[b]{platform.node()}[/]"
        #     + f" {self.distro_string}"
        self.left_string = " ".join(
            [
                f"[b]{platform.node()}[/]",
                f"{ri['name']} {ri['version_id']}",
                f"{platform.architecture()[0]} / {platform.release()}",
            ]
        )

    def render(self):
        # now = datetime.now().strftime("%c")

        table = Table(show_header=False, expand=True, box=None, padding=0)
        table.add_column(justify="left", no_wrap=True)
        table.add_column(justify="right", no_wrap=True)

        uptime_s = time.time() - psutil.boot_time()
        d = datetime(1, 1, 1) + timedelta(seconds=uptime_s)
        battery = psutil.sensors_battery().percent
        bat_style = "[color(1) reverse bold]" if battery < 15 else ""
        bat_style_close = "[/]" if battery < 15 else ""
        bat_symbol = "🔌" if psutil.sensors_battery().power_plugged else "🔋"
        right = ", ".join(
            [
                f"up {d.day - 1}d, {d.hour}:{d.minute:02d}h",
                f"{bat_symbol} {bat_style}{round(battery)}%{bat_style_close}",
            ]
        )

        table.add_row(self.left_string, right)
        return table


class CPU(Widget):
    def on_mount(self):
        self.data = []
        self.num_cores = psutil.cpu_count(logical=False)
        self.num_threads = psutil.cpu_count(logical=True)

        self.cpu_total_stream = BrailleStream(50, 6, 0.0, 100.0)

        self.cpu_percent_streams = [
            BrailleStream(10, 1, 0.0, 100.0)
            for _ in range(self.num_threads)
            # BlockCharStream(10, 1, 0.0, 100.0) for _ in range(self.num_threads)
        ]

        temp_low = 20.0
        temp_high = psutil.sensors_temperatures()["coretemp"][0].high
        self.temp_total_stream = BrailleStream(50, 6, temp_low, temp_high, flipud=True)
        self.core_temp_streams = [
            BrailleStream(5, 1, temp_low, temp_high) for _ in range(self.num_cores)
        ]

        self.box_title = ", ".join(
            [
                f"{self.num_threads} threads",
                f"{self.num_cores} cores",
            ]
        )

        self.brand_raw = cpuinfo.get_cpu_info()["brand_raw"]

        self.collect_data()
        self.set_interval(2.0, self.collect_data)

    def collect_data(self):
        # CPU loads
        self.cpu_total_stream.add_value(psutil.cpu_percent())
        #
        load_indiv = psutil.cpu_percent(percpu=True)
        cpu_percent_colors = [val_to_color(val, 0.0, 100.0) for val in load_indiv]
        for stream, load in zip(self.cpu_percent_streams, load_indiv):
            stream.add_value(load)

        # CPU temperatures
        temps = psutil.sensors_temperatures()["coretemp"]
        self.temp_total_stream.add_value(temps[0].current)
        #
        for stream, temp in zip(self.core_temp_streams, temps[1:]):
            stream.add_value(temp.current)

        lines_cpu = self.cpu_total_stream.graph
        last_val_string = f"{self.cpu_total_stream.last_value:5.1f}%"
        lines0 = lines_cpu[0][: -len(last_val_string)] + last_val_string
        self.lines_cpu = [lines0] + lines_cpu[1:]
        #
        lines_temp = self.temp_total_stream.graph
        last_val_string = f"{round(self.temp_total_stream.last_value):3d}°C"
        lines0 = lines_temp[-1][: -len(last_val_string)] + last_val_string
        lines_temp = lines_temp[:-1] + [lines0]
        #
        cpu_total_graph = align.Align(
            "[color(4)]"
            + "\n".join(lines_cpu)
            + "[/]\n"
            + "[color(5)]"
            + "\n".join(lines_temp)
            + "[/]"
        )

        # threads 0 and 4 are in one core, display them next to each other, etc.
        cores = [0, 4, 1, 5, 2, 6, 3, 7]
        lines = [
            f"[{cpu_percent_colors[i]}]"
            + f"{self.cpu_percent_streams[i].graph[0]} "
            + f"{round(self.cpu_percent_streams[i].last_value):3d}%[/]"
            for i in cores
        ]
        # add temperature in every other line
        for k, stream in enumerate(self.core_temp_streams):
            lines[
                2 * k
            ] += f" [color(5)]{stream.graph[0]} {round(stream.last_value)}°C[/]"

        # load_avg = os.getloadavg()
        # subtitle = f"Load Avg:  {load_avg[0]:.2f}  {load_avg[1]:.2f}  {load_avg[2]:.2f}"
        subtitle = f"{round(psutil.cpu_freq().current):4d} MHz"

        info_box = align.Align(
            Panel(
                "\n".join(lines),
                title=self.box_title,
                title_align="left",
                subtitle=subtitle,
                subtitle_align="left",
                border_style="color(7)",
                box=box.SQUARE,
            ),
            "right",
            vertical="middle",
        )

        t = Table(expand=True, show_header=False, padding=0)
        t.add_column("graph", no_wrap=True, justify="right")
        t.add_column("box", no_wrap=True)
        # t.add_row(", ".join(["dasdas\n"] * 100), info_box)
        t.add_row(cpu_total_graph, info_box)
        # c = Columns(["dasdas", info_box], expand=True)

        self.panel = Panel(
            t,
            title=f"cpu - {self.brand_raw}",
            title_align="left",
            border_style="color(4)",
            box=box.SQUARE,
        )

        # textual method
        self.refresh()

    def render(self):
        return self.panel


class Mem(Widget):
    def on_mount(self):
        self.mem_total_bytes = psutil.virtual_memory().total
        self.mem_total_string = sizeof_fmt(self.mem_total_bytes, fmt=".2f")

        self.mem_streams = [
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
            BrailleStream(40, 4, 0.0, self.mem_total_bytes),
        ]

        self.collect_data()
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
                    [val_string + stream.graph[0][: -len(val_string)]]
                    + stream.graph[1:]
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
        return self.panel


class ProcsList(Widget):
    def on_mount(self):
        self.collect_data()
        self.set_interval(6.0, self.collect_data)

    def collect_data(self):
        attrs = [
            "pid",
            "name",
            "username",
            "cmdline",
            "cpu_percent",
            "num_threads",
            "memory_info",
        ]
        processes = sorted(
            psutil.process_iter(attrs),
            key=lambda item: item.info["cpu_percent"],
            reverse=True,
        )

        table = Table(
            show_header=True,
            header_style="bold",
            box=None,
            padding=0,
            expand=True,
            # border_style=None,
        )
        table.add_column("pid", min_width=6, no_wrap=True)
        table.add_column("program", max_width=10, style="color(2)", no_wrap=True)
        table.add_column("args", max_width=20, no_wrap=True)
        table.add_column("#th", width=3, style="color(2)", no_wrap=True)
        table.add_column("user", no_wrap=True)
        table.add_column("mem", style="color(2)", no_wrap=True)
        table.add_column("[u]cpu%[/]", width=5, style="color(2)", no_wrap=True)

        for p in processes[:30]:
            table.add_row(
                f"{p.info['pid']:6d}",
                p.info["name"],
                " ".join(p.info["cmdline"][1:]),
                f"{p.info['num_threads']:3d}",
                p.info["username"],
                sizeof_fmt(p.info["memory_info"].rss, suffix="", sep=""),
                f"{p.info['cpu_percent']:5.1f}",
            )

        self.panel = Panel(
            table,
            title="proc",
            title_align="left",
            border_style="color(6)",
            box=box.SQUARE,
        )

        self.refresh()

    def render(self) -> Panel:
        return self.panel


class Net(Widget):
    def on_mount(self):
        # try to find non-lo interface that is up
        self.interface = None
        stats = psutil.net_if_stats()
        for string, stats in stats.items():
            if string != "lo" and stats.isup:
                self.interface = string
                break

        if self.interface is None:
            assert "lo" in stats
            self.interface = "lo"

        self.last_net = None
        self.max_recv_bytes_s = 0
        self.max_recv_bytes_s_str = ""
        self.max_sent_bytes_s = 0
        self.max_sent_bytes_s_str = ""

        self.recv_stream = BrailleStream(20, 5, 0.0, 1.0e6)
        self.sent_stream = BrailleStream(20, 5, 0.0, 1.0e6, flipud=True)

        self.update_ip()
        self.collect_data()

        self.interval_s = 2.0
        self.set_interval(self.interval_s, self.collect_data)

    def update_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip = s.getsockname()[0]
        s.close()

    def collect_data(self):
        self.ipv4 = None
        for addr in psutil.net_if_addrs()[self.interface]:
            # ipv4?
            if addr.family == socket.AF_INET:
                self.ipv4 = addr.address
                break

        net = psutil.net_io_counters(pernic=True)[self.interface]
        if self.last_net is None:
            recv_bytes_s_string = ""
            sent_bytes_s_string = ""
        else:
            recv_bytes_s = (net.bytes_recv - self.last_net.bytes_recv) / self.interval_s
            recv_bytes_s_string = sizeof_fmt(recv_bytes_s, fmt=".1f") + "/s"
            sent_bytes_s = (net.bytes_sent - self.last_net.bytes_sent) / self.interval_s
            sent_bytes_s_string = sizeof_fmt(sent_bytes_s, fmt=".1f") + "/s"

            if recv_bytes_s > self.max_recv_bytes_s:
                self.max_recv_bytes_s = recv_bytes_s
                self.max_recv_bytes_s_str = sizeof_fmt(recv_bytes_s, fmt=".1f") + "/s"

            if sent_bytes_s > self.max_sent_bytes_s:
                self.max_sent_bytes_s = sent_bytes_s
                self.max_sent_bytes_s_str = sizeof_fmt(sent_bytes_s, fmt=".1f") + "/s"

            self.recv_stream.add_value(recv_bytes_s)
            self.sent_stream.add_value(sent_bytes_s)

        self.last_net = net

        total_recv_string = sizeof_fmt(net.bytes_recv, sep=" ", fmt=".1f")
        total_sent_string = sizeof_fmt(net.bytes_sent, sep=" ", fmt=".1f")

        down_box_lines = [
            f"{recv_bytes_s_string}",
            f"max   {self.max_recv_bytes_s_str}",
            f"total {total_recv_string}",
        ]
        down_box = Panel(
            "\n".join(down_box_lines),
            title="▼ down",
            title_align="left",
            style="color(2)",
            width=20,
            box=box.SQUARE,
        )
        up_box_lines = [
            f"{sent_bytes_s_string}",
            f"max   {self.max_sent_bytes_s_str}",
            f"total {total_sent_string}",
        ]
        up_box = Panel(
            "\n".join(up_box_lines),
            title="▲ up",
            title_align="left",
            style="color(4)",
            width=20,
            box=box.SQUARE,
        )

        t = Table(expand=True, show_header=False, padding=0)
        t.add_column("graph", no_wrap=True, justify="right")
        t.add_column("box", no_wrap=True, width=down_box.width)

        t.add_row("[color(2)]" + "\n".join(self.recv_stream.graph) + "[/]", down_box)
        t.add_row("[color(4)]" + "\n".join(self.sent_stream.graph) + "[/]", up_box)

        self.content = Panel(
            t,
            title=f"net - {self.interface}",
            border_style="color(1)",
            title_align="left",
            box=box.SQUARE,
        )

        self.refresh()

    def render(self):
        return self.content


# class TiptopApp(App):
#     async def on_mount(self) -> None:
#         await self.view.dock(InfoLine(), edge="top", size=1, name="info")
#         await self.view.dock(CPU(), edge="top", size=14, name="cpu")
#         await self.view.dock(ProcsList(), edge="right", size=70, name="proc")
#         await self.view.dock(Mem(), edge="top", size=20, name="mem")
#         await self.view.dock(Net(), edge="bottom", name="net")
#
#     async def on_load(self, _):
#         await self.bind("i", "view.toggle('info')", "Toggle info")
#         await self.bind("c", "view.toggle('cpu')", "Toggle cpu")
#         await self.bind("m", "view.toggle('mem')", "Toggle mem")
#         await self.bind("n", "view.toggle('net')", "Toggle net")
#         await self.bind("p", "view.toggle('proc')", "Toggle proc")
#         await self.bind("q", "quit", "quit")


# with a grid
class TiptopApp(App):
    async def on_mount(self) -> None:
        grid = await self.view.dock_grid(edge="left")

        grid.add_column(fraction=1, name="left")
        grid.add_column(fraction=1, name="right")

        grid.add_row(size=1, name="topline")
        grid.add_row(fraction=1, name="top")
        grid.add_row(fraction=1, name="center")
        grid.add_row(fraction=1, name="bottom")

        grid.add_areas(
            area0="left-start|right-end,topline",
            area1="left-start|right-end,top",
            area2="left,center",
            area3="left,bottom",
            area4="right,center-start|bottom-end",
        )

        grid.place(
            area0=InfoLine(), area1=CPU(), area2=Mem(), area3=Net(), area4=ProcsList()
        )

    async def on_load(self, _):
        await self.bind("q", "quit", "quit")


TiptopApp.run()
