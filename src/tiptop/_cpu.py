import cpuinfo
import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from .braille_stream import BrailleStream


def val_to_color(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = round(t * 3)
    return {0: "color(4)", 1: "color(6)", 2: "color(6)", 3: "color(2)"}[k]


# https://stackoverflow.com/a/312464/353337
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# https://stackoverflow.com/a/6473724/353337
def transpose(lst):
    return list(map(list, zip(*lst)))


def flatten(lst):
    return [item for sublist in lst for item in sublist]


class CPU(Widget):
    def on_mount(self):
        self.width = None
        self.height = None

        # self.max_graph_width = 200

        num_cores = psutil.cpu_count(logical=False)
        num_threads = psutil.cpu_count(logical=True)

        # 8 threads, 4 cores -> [0, 4, 1, 5, 2, 6, 3, 7]
        assert num_threads % num_cores == 0
        self.core_order = flatten(
            transpose(list(chunks(range(num_threads), num_cores)))
        )

        self.cpu_total_stream = BrailleStream(50, 7, 0.0, 100.0)

        self.cpu_percent_streams = [
            BrailleStream(10, 1, 0.0, 100.0)
            for _ in range(num_threads)
            # BlockCharStream(10, 1, 0.0, 100.0) for _ in range(num_threads)
        ]

        try:
            temps = psutil.sensors_temperatures()
        except AttributeError:
            self.has_temps = False
        else:
            self.has_temps = "coretemp" in temps
            if self.has_temps:
                temp_low = 20.0
                temp_high = temps["coretemp"][0].high
                assert temp_high is not None
                self.temp_total_stream = BrailleStream(
                    50, 7, temp_low, temp_high, flipud=True
                )
                self.core_temp_streams = [
                    BrailleStream(5, 1, temp_low, temp_high) for _ in range(num_cores)
                ]

        self.box_title = ", ".join(
            [
                f"{num_threads} thread" + "s" if num_threads > 1 else "",
                f"{num_cores} core" + "s" if num_cores > 1 else "",
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
        if self.has_temps:
            coretemps = psutil.sensors_temperatures()["coretemp"]
            self.temp_total_stream.add_value(coretemps[0].current)
            #
            for stream, temp in zip(self.core_temp_streams, coretemps[1:]):
                stream.add_value(temp.current)

        lines_cpu = self.cpu_total_stream.graph
        last_val_string = f"{self.cpu_total_stream.values[-1]:5.1f}%"
        lines0 = lines_cpu[0][: -len(last_val_string)] + last_val_string
        lines_cpu = [lines0] + lines_cpu[1:]
        #
        cpu_total_graph = "[color(4)]" + "\n".join(lines_cpu) + "[/]\n"

        #
        if self.has_temps:
            lines_temp = self.temp_total_stream.graph
            last_val_string = f"{round(self.temp_total_stream.values[-1]):3d}°C"
            lines0 = lines_temp[-1][: -len(last_val_string)] + last_val_string
            lines_temp = lines_temp[:-1] + [lines0]
            cpu_total_graph += "[color(5)]" + "\n".join(lines_temp) + "[/]"

        lines = [
            f"[{cpu_percent_colors[i]}]"
            + f"{self.cpu_percent_streams[i].graph[0]} "
            + f"{round(self.cpu_percent_streams[i].values[-1]):3d}%[/]"
            for i in self.core_order
        ]
        if self.has_temps:
            # add temperature in every other line
            for k, stream in enumerate(self.core_temp_streams):
                lines[
                    2 * k
                ] += f" [color(5)]{stream.graph[0]} {round(stream.values[-1])}°C[/]"

        # load_avg = os.getloadavg()
        # subtitle = f"Load Avg:  {load_avg[0]:.2f}  {load_avg[1]:.2f}  {load_avg[2]:.2f}"
        subtitle = f"{round(psutil.cpu_freq().current):4d} MHz"

        info_box = Panel(
            "\n".join(lines),
            title=self.box_title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="left",
            border_style="color(7)",
            box=box.SQUARE,
            expand=False,
        )

        t = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        t.add_column("graph", no_wrap=True, ratio=1)
        t.add_column("box", no_wrap=True, justify="left")
        # waiting for vertical alignment in rich here
        # <https://github.com/willmcgugan/rich/issues/1590>
        t.add_row(cpu_total_graph, info_box)

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

    async def on_resize(self, event):
        self.width = event.width
        self.height = event.height

        self.cpu_total_stream.reset_width(self.width - 35)

        if self.has_temps:
            # cpu total stream height: divide by two and round _up_
            self.cpu_total_stream.reset_height(-((2 - self.height) // 2))
            #
            self.temp_total_stream.reset_width(self.width - 35)
            # temp total stream height: divide by two and round _down_
            self.temp_total_stream.reset_height((self.height - 2) // 2)
        else:
            # full size cpu stream
            self.cpu_total_stream.reset_height(self.height - 2)
