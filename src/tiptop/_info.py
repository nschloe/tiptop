import os
import platform
import time
from datetime import datetime, timedelta

import distro
import psutil
from rich.table import Table
from textual.widget import Widget


class InfoLine(Widget):
    def on_mount(self):
        self.width = 0
        self.height = 0
        self.set_interval(2.0, self.refresh)
        ri = distro.os_release_info()
        self.left_string = " ".join(
            [
                f"{os.getlogin()} @ [b]{platform.node()}[/]",
                f"{ri['name']} {ri['version_id']}",
                f"{platform.architecture()[0]} / {platform.release()}",
            ]
        )
        self.boot_time = psutil.boot_time()

    def render(self):
        uptime_s = time.time() - self.boot_time
        d = datetime(1, 1, 1) + timedelta(seconds=uptime_s)
        right = [f"up {d.day - 1}d, {d.hour}:{d.minute:02d}h"]

        battery = psutil.sensors_battery()
        if battery is not None:
            bat_style = "[color(1) reverse bold]" if battery.percent < 15 else ""
            bat_style_close = "[/]" if battery.percent < 15 else ""
            bat_symbol = "🔌" if battery.power_plugged else "🔋"
            right.append(
                f"{bat_style}{bat_symbol} {round(battery.percent)}%{bat_style_close}"
            )

        table = Table(show_header=False, expand=True, box=None, padding=0)
        if self.width < 100:
            table.add_column(justify="left", no_wrap=True)
            table.add_column(justify="right", no_wrap=True)
            table.add_row(self.left_string, ", ".join(right))
        else:
            table.add_column(justify="left", no_wrap=True, ratio=1)
            table.add_column(justify="center", no_wrap=True, ratio=1)
            table.add_column(justify="right", no_wrap=True, ratio=1)
            table.add_row(
                self.left_string, datetime.now().strftime("%c"), ", ".join(right)
            )
        return table

    async def on_resize(self, event):
        self.width = event.width
        self.height = event.height
