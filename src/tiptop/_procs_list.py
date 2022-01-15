import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from .__about__ import __version__
from ._helpers import sizeof_fmt


class ProcsList(Widget):
    def on_mount(self):
        self.tiptop_string = f"tiptop v{__version__}"
        self.max_num_procs = 100
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
            "status",
        ]
        processes = sorted(
            psutil.process_iter(attrs),
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
            padding=0,
            expand=True,
        )
        table.add_column("pid", min_width=6, no_wrap=True)
        table.add_column("program", max_width=10, style="green", no_wrap=True)
        table.add_column("args", max_width=20, no_wrap=True)
        table.add_column("thr", width=3, style="green", no_wrap=True)
        table.add_column("user", no_wrap=True)
        table.add_column("mem", style="green", no_wrap=True)
        table.add_column("[u]cpu%[/]", width=5, no_wrap=True)

        for p in processes[: self.max_num_procs]:
            # Everything can be None here, see comment above
            pid = p.info["pid"]
            pid = "" if pid is None else f"{pid:6d}"
            #
            name = p.info["name"]
            if name is None:
                name = ""
            #
            cmdline = p.info["cmdline"]
            cmdline = "" if cmdline is None else " ".join(p.info["cmdline"][1:])
            #
            num_threads = p.info["num_threads"]
            num_threads = "" if num_threads is None else f"{num_threads:3d}"
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
            cpu_percent = "" if cpu_percent is None else f"{cpu_percent:5.1f}"
            table.add_row(
                pid, name, cmdline, num_threads, username, mem_info, cpu_percent
            )

        total_num_threads = sum((p.info["num_threads"] or 0) for p in processes)
        num_sleep = sum(p.info["status"] == "sleeping" for p in processes)

        self.panel = Panel(
            table,
            title=f"proc - {len(processes)} ({total_num_threads} thr), {num_sleep} slp",
            title_align="left",
            subtitle=self.tiptop_string,
            subtitle_align="right",
            border_style="cyan",
            box=box.SQUARE,
        )

        self.refresh()

    def render(self) -> Panel:
        return self.panel

    async def on_resize(self, event):
        self.max_num_procs = event.height - 3
