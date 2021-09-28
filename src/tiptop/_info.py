import platform
import time
from datetime import datetime, timedelta

import distro
import psutil
from rich.table import Table
from textual.widget import Widget


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
        right = [f"up {d.day - 1}d, {d.hour}:{d.minute:02d}h"]

        battery = psutil.sensors_battery()
        if battery is not None:
            bat_style = "[color(1) reverse bold]" if battery.percent < 15 else ""
            bat_style_close = "[/]" if battery.percent < 15 else ""
            bat_symbol = "🔌" if battery.power_plugged else "🔋"
            right.append(f"{bat_style}{bat_symbol} {round(battery.percent)}%{bat_style_close}")

        table.add_row(self.left_string, ", ".join(right))
        return table
