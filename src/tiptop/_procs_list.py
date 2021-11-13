import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from ._helpers import sizeof_fmt


class ProcsList(Widget):
    def on_mount(self):
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
            key=lambda item: item.info["cpu_percent"],
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
        table.add_column("program", max_width=10, style="color(2)", no_wrap=True)
        table.add_column("args", max_width=20, no_wrap=True)
        table.add_column("thr", width=3, style="color(2)", no_wrap=True)
        table.add_column("user", no_wrap=True)
        table.add_column("mem", style="color(2)", no_wrap=True)
        table.add_column("[u]cpu%[/]", width=5, no_wrap=True)

        for p in processes[: self.max_num_procs]:
            table.add_row(
                f"{p.info['pid']:6d}",
                p.info["name"],
                " ".join(p.info["cmdline"][1:]),
                f"{p.info['num_threads']:3d}",
                p.info["username"],
                sizeof_fmt(p.info["memory_info"].rss, suffix="", sep=""),
                f"{p.info['cpu_percent']:5.1f}",
            )

        total_num_threads = sum(p.info["num_threads"] for p in processes)
        num_sleep = sum(p.info["status"] == "sleeping" for p in processes)

        self.panel = Panel(
            table,
            title=f"proc - {len(processes)} ({total_num_threads} thr), {num_sleep} slp",
            title_align="left",
            border_style="color(6)",
            box=box.SQUARE,
        )

        self.refresh()

    def render(self) -> Panel:
        return self.panel

    async def on_resize(self, event):
        self.max_num_procs = event.height - 3
