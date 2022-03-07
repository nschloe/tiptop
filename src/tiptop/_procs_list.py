import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widget import Widget

from ._helpers import sizeof_fmt


class ProcsList(Widget):
    def on_mount(self):
        self.max_num_procs = 100
        self.collect_data()
        self.set_interval(6.0, self.collect_data)

    def collect_data(self):
        processes = list(
            psutil.process_iter(
                [
                    "pid",
                    "name",
                    "username",
                    "cmdline",
                    "cpu_percent",
                    "num_threads",
                    "memory_info",
                    "status",
                ]
            )
        )

        if processes[0].pid == 0:
            # Remove process with PID 0. On Windows, that's SYSTEM IDLE, and we
            # don't want that to appear at the top of the list.
            # <https://twitter.com/andre_roberge/status/1488885893716975622/photo/1>
            processes = processes[1:]

        processes = sorted(
            processes,
            # The item.info["cpu_percent"] can be `ad_value` (default None).
            # It gets assigned to a dict key in case AccessDenied or
            # ZombieProcess exception is raised when retrieving that particular
            # process information.
            key=lambda item: (item.info["cpu_percent"] or 0.0),
            reverse=True,
        )

        table = Table(
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
            expand=True,
        )
        # set ration=1 on all columns that should be expanded
        # <https://github.com/Textualize/rich/issues/2030>
        table.add_column(Text("pid", justify="left"), no_wrap=True, justify="right")
        table.add_column("program", style="green", no_wrap=True, ratio=1)
        table.add_column("args", no_wrap=True, ratio=2)
        table.add_column(
            Text("thr", justify="left"),
            style="green",
            no_wrap=True,
            justify="right",
        )
        table.add_column("user", no_wrap=True)
        table.add_column(
            Text("mem", justify="left"), style="green", no_wrap=True, justify="right"
        )
        table.add_column(
            Text("cpu%", style="u", justify="left"),
            no_wrap=True,
            justify="right",
        )

        for p in processes[: self.max_num_procs]:
            # Everything can be None here, see comment above
            pid = p.info["pid"]
            pid = "" if pid is None else str(pid)
            #
            name = p.info["name"]
            if name is None:
                name = ""
            #
            cmdline = p.info["cmdline"]
            cmdline = "" if cmdline is None else " ".join(p.info["cmdline"][1:])
            #
            num_threads = p.info["num_threads"]
            num_threads = "" if num_threads is None else str(num_threads)
            #
            username = p.info["username"]
            if username is None:
                username = ""
            #
            mem_info = p.info["memory_info"]
            mem_info = (
                "" if mem_info is None else sizeof_fmt(mem_info.rss, suffix="", sep="")
            )
            #
            cpu_percent = p.info["cpu_percent"]
            cpu_percent = "" if cpu_percent is None else f"{cpu_percent:.1f}"
            table.add_row(
                pid, name, cmdline, num_threads, username, mem_info, cpu_percent
            )

        total_num_threads = sum((p.info["num_threads"] or 0) for p in processes)
        num_sleep = sum(p.info["status"] == "sleeping" for p in processes)

        self.panel = Panel(
            table,
            title=f"[b]proc[/] - {len(processes)} ({total_num_threads} thr), {num_sleep} slp",
            title_align="left",
            # border_style="cyan",
            border_style="white",
            box=box.SQUARE,
        )

        self.refresh()

    def render(self) -> Panel:
        return self.panel

    async def on_resize(self, event):
        self.max_num_procs = event.height - 3
