import cpuinfo
import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
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

        self.tempkey = None
        self.has_cpu_temp = False
        self.has_core_temps = False

        try:
            temps = psutil.sensors_temperatures()
        except AttributeError:
            pass
        else:
            # coretemp: intel, k10temp: amd
            # <https://github.com/nschloe/tiptop/issues/37>
            for key in ["coretemp", "k10temp"]:
                if key in temps:
                    self.tempkey = key
                    self.has_cpu_temp = len(temps[key]) > 0
                    self.has_core_temps = len(temps[key]) == 1 + self.num_cores
                    break

            temp_low = 30.0

            if self.has_cpu_temp:
                assert self.tempkey is not None
                self.temp_total_stream = BrailleStream(
                    50, 7, temp_low, temps[self.tempkey][0].high or 100.0, flipud=True
                )

            if self.has_core_temps:
                assert self.tempkey is not None
                self.core_temp_streams = [
                    BrailleStream(
                        5,
                        1,
                        temp_low,
                        temps[self.tempkey][k + 1].high
                        or temps[self.tempkey][0].high
                        or 100.0,
                    )
                    for k in range(self.num_cores)
                ]

        self.has_fan_rpm = False
        try:
            fan_current = list(psutil.sensors_fans().values())[0][0].current
        except (AttributeError, IndexError):
            pass
        else:
            self.has_fan_rpm = True
            fan_low = 0
            # Sometimes, psutil/computers will incorrectly report a fan
            # speed of 2 ** 16 - 1; dismiss that.
            if fan_current == 65535:
                fan_current = 1
            fan_high = max(fan_current, 1)
            self.fan_stream = BrailleStream(50, 1, fan_low, fan_high)

        box_title = ", ".join(
            [
                f"{self.num_cores} core" + ("s" if self.num_cores > 1 else ""),
                f"{num_threads} thread" + ("s" if num_threads > 1 else ""),
            ]
        )
        self.info_box = Panel(
            "",
            title=box_title,
            title_align="left",
            subtitle=None,
            subtitle_align="left",
            border_style="white",
            box=box.SQUARE,
            expand=False,
        )

        brand_raw = cpuinfo.get_cpu_info()["brand_raw"]
        self.panel = Panel(
            "",
            title=f"[b]cpu[/] - {brand_raw}",
            title_align="left",
            border_style="white",
            box=box.SQUARE,
        )

        # immediately collect data to refresh info_box_width
        self.collect_data()
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
        if self.has_cpu_temp or self.has_core_temps:
            temps = psutil.sensors_temperatures()

            if self.has_cpu_temp:
                assert self.tempkey is not None
                self.temp_total_stream.add_value(temps[self.tempkey][0].current)

            if self.has_core_temps:
                assert self.tempkey is not None
                for stream, temp in zip(
                    self.core_temp_streams, temps[self.tempkey][1:]
                ):
                    stream.add_value(temp.current)

        lines_cpu = self.cpu_total_stream.graph
        current_val_string = f"{self.cpu_total_stream.values[-1]:5.1f}%"
        lines0 = lines_cpu[0][: -len(current_val_string)] + current_val_string
        lines_cpu = [lines0] + lines_cpu[1:]
        #
        cpu_total_graph = "[blue]" + "\n".join(lines_cpu) + "[/]\n"
        #
        if self.has_cpu_temp:
            lines_temp = self.temp_total_stream.graph
            current_val_string = f"{round(self.temp_total_stream.values[-1]):3d}°C"
            lines0 = lines_temp[-1][: -len(current_val_string)] + current_val_string
            lines_temp = lines_temp[:-1] + [lines0]
            cpu_total_graph += "[magenta]" + "\n".join(lines_temp) + "[/]"

        # construct right info box
        self._refresh_info_box(load_per_thread)

        t = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        t.add_column("graph", no_wrap=True, ratio=1)
        t.add_column("box", no_wrap=True, justify="left", vertical="middle")
        t.add_row(cpu_total_graph, self.info_box)

        if self.has_fan_rpm:
            fan_current = list(psutil.sensors_fans().values())[0][0].current

            # See command above
            if fan_current == 65535:
                fan_current = self.fan_stream.maxval

            if fan_current > self.fan_stream.maxval:
                # TODO There should be a method that also rewrites all previous values
                self.fan_stream.maxval = fan_current

            self.fan_stream.add_value(fan_current)
            string = f" {fan_current}rpm"
            graph = (
                "[cyan]" + self.fan_stream.graph[-1][: -len(string)] + string + "[/]"
            )
            t.add_row(graph, "")

        self.panel.renderable = t

        # textual method
        self.refresh()

    def _refresh_info_box(self, load_per_thread):
        lines = []
        for core_id, thread_ids in enumerate(self.core_threads):
            line = []
            for i in thread_ids:
                color = val_to_color(load_per_thread[i], 0.0, 100.0)
                line.append(
                    f"[{color}]"
                    + f"{self.thread_load_streams[i].graph[0]}"
                    + f"{round(self.thread_load_streams[i].values[-1]):3d}%"
                    + "[/]"
                )
            if self.has_core_temps:
                stream = self.core_temp_streams[core_id]
                val = stream.values[-1]
                color = "magenta" if val < 70.0 else "red"
                line.append(
                    f"[{color}]{stream.graph[0]} {round(stream.values[-1])}°C[/]"
                )

            lines.append(" ".join(line))

        self.info_box.renderable = "\n".join(lines)

        try:
            cpu_freq = psutil.cpu_freq().current
        except Exception:
            # https://github.com/nschloe/tiptop/issues/25
            self.info_box.subtitle = None
        else:
            if psutil.__version__ == "5.9.0":
                # Work around
                # https://github.com/giampaolo/psutil/issues/2049
                cpu_freq *= 1000
            self.info_box.subtitle = f"{round(cpu_freq):4d} MHz"

        # https://github.com/willmcgugan/rich/discussions/1559#discussioncomment-1459008
        self.info_box_width = 4 + len(Text.from_markup(lines[0]))

    def render(self):
        return self.panel

    async def on_resize(self, event):
        self.width = event.width
        self.height = event.height

        # reset graph widths
        graph_width = self.width - self.info_box_width - 5
        self.cpu_total_stream.reset_width(graph_width)
        if self.has_cpu_temp:
            self.temp_total_stream.reset_width(graph_width)
        if self.has_fan_rpm:
            self.fan_stream.reset_width(graph_width)

        # reset graph heights
        # subtract border
        total_height = self.height - 2
        if self.has_cpu_temp:
            # cpu total stream height: divide by two and round _down_
            self.cpu_total_stream.reset_height(total_height // 2)
            #
            # temp total stream height: divide by two and round _up_. Subtract
            # one if a fan stream is present.
            temp_stream_height = -((-total_height) // 2)
            if self.has_fan_rpm:
                temp_stream_height -= 1

            self.temp_total_stream.reset_height(temp_stream_height)
        else:
            # full size cpu stream
            cpu_stream_height = total_height
            if self.has_fan_rpm:
                cpu_stream_height -= 1

            self.cpu_total_stream.reset_height(cpu_stream_height)
