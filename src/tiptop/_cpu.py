import cpuinfo
import psutil
from rich import box
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from .braille_stream import BrailleStream


def val_to_color(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = round(t * 3)
    return {0: "blue", 1: "cyan", 2: "cyan", 3: "green"}[k]


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
        self.is_first_render = True
        self.width = 0
        self.height = 0

        # self.max_graph_width = 200

        self.num_cores = psutil.cpu_count(logical=False)
        num_threads = psutil.cpu_count(logical=True)

        # 8 threads, 4 cores -> [[0, 4], [1, 5], [2, 6], [3, 7]]
        assert num_threads % self.num_cores == 0
        self.core_threads = transpose(list(chunks(range(num_threads), self.num_cores)))

        self.cpu_total_stream = BrailleStream(50, 7, 0.0, 100.0)

        self.thread_load_streams = [
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
                    BrailleStream(5, 1, temp_low, temp_high)
                    for _ in range(self.num_cores)
                ]

        self.box_title = ", ".join(
            [
                f"{num_threads} thread" + ("s" if num_threads > 1 else ""),
                f"{self.num_cores} core" + ("s" if self.num_cores > 1 else ""),
            ]
        )

        self.brand_raw = cpuinfo.get_cpu_info()["brand_raw"]
        self.set_interval(2.0, self.collect_data)

    def collect_data(self):
        # CPU loads
        self.cpu_total_stream.add_value(psutil.cpu_percent())
        #
        load_per_thread = psutil.cpu_percent(percpu=True)
        assert isinstance(load_per_thread, list)
        for stream, load in zip(self.thread_load_streams, load_per_thread):
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
        cpu_total_graph = "[blue]" + "\n".join(lines_cpu) + "[/]\n"
        #
        if self.has_temps:
            lines_temp = self.temp_total_stream.graph
            last_val_string = f"{round(self.temp_total_stream.values[-1]):3d}°C"
            lines0 = lines_temp[-1][: -len(last_val_string)] + last_val_string
            lines_temp = lines_temp[:-1] + [lines0]
            cpu_total_graph += "[magenta]" + "\n".join(lines_temp) + "[/]"

        # construct right info box
        info_box, info_box_height = self._construct_info_box(load_per_thread)

        # Manually adjust top margin. Waiting for vertical alignment in Rich.
        # <https://github.com/willmcgugan/rich/issues/1590>
        top_margin = (self.height - 2 - info_box_height) // 2
        info_box = Padding(info_box, (top_margin, 0, 0, 0))

        t = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        t.add_column("graph", no_wrap=True, ratio=1)
        t.add_column("box", no_wrap=True, justify="left")
        t.add_row(cpu_total_graph, info_box)

        self.panel = Panel(
            t,
            title=f"cpu - {self.brand_raw}",
            title_align="left",
            border_style="blue",
            box=box.SQUARE,
        )

        # textual method
        self.refresh()

    def _construct_info_box(self, load_per_thread):
        thread_load_graphs = []
        for core_id, thread_ids in enumerate(self.core_threads):
            for i in thread_ids:
                color = val_to_color(load_per_thread[i], 0.0, 100.0)
                thread_load_graphs.append(
                    f"[{color}]"
                    + f"{self.thread_load_streams[i].graph[0]} "
                    + f"{round(self.thread_load_streams[i].values[-1]):3d}%"
                    + "[/]"
                )
        #
        core_temp_graphs = []
        if self.has_temps:
            for core_id in range(self.num_cores):
                stream = self.core_temp_streams[core_id]
                core_temp_graphs.append(
                    f"[magenta]{stream.graph[0]} {round(stream.values[-1])}°C[/]"
                )
        #
        # merge thread load graphs and core temp graphs into a table structure
        lines = []
        for core_id, thread_ids in enumerate(self.core_threads):
            new_lines = [thread_load_graphs[i] for i in thread_ids]
            if self.has_temps:
                new_lines[0] += " " + core_temp_graphs[core_id]
            lines += new_lines

        info_box_content = "\n".join(lines)

        try:
            cpu_freq = psutil.cpu_freq().current
        except Exception:
            # https://github.com/nschloe/tiptop/issues/25
            subtitle = None
        else:
            subtitle = f"{round(cpu_freq):4d} MHz"

        info_box = Panel(
            info_box_content,
            title=self.box_title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="left",
            border_style="white",
            box=box.SQUARE,
            expand=False,
        )
        return info_box, len(lines) + 2

    def render(self):
        if self.is_first_render:
            self.collect_data()
            self.is_first_render = False
        return self.panel

    async def on_resize(self, event):
        self.width = event.width
        self.height = event.height

        self.cpu_total_stream.reset_width(self.width - 35)

        if self.has_temps:
            # cpu total stream height: divide by two and round _down_
            self.cpu_total_stream.reset_height((self.height - 2) // 2)
            #
            self.temp_total_stream.reset_width(self.width - 35)
            # temp total stream height: divide by two and round _up_
            self.temp_total_stream.reset_height(-((2 - self.height) // 2))
        else:
            # full size cpu stream
            self.cpu_total_stream.reset_height(self.height - 2)
