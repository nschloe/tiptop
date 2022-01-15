import getpass
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
        self.set_interval(1.0, self.refresh)

        # The getlogin docs say:
        # > For most purposes, it is more useful to use getpass.getuser() [...]
        # username = os.getlogin()
        username = getpass.getuser()
        ustring = f"{username} @"
        node = platform.node()
        if node:
            ustring += f" [b]{platform.node()}[/]"

        system = platform.system()
        if system == "Linux":
            ri = distro.os_release_info()
            system_list = [ri["name"]]
            if "version_id" in ri:
                system_list.append(ri["version_id"])
            system_list.append(f"{platform.architecture()[0]} / {platform.release()}")
            system_string = " ".join(system_list)
        elif system == "Darwin":
            system_string = f"macOS {platform.mac_ver()[0]}"
        else:
            # fallback
            system_string = ""

        self.left_string = " ".join([ustring, system_string])
        self.boot_time = psutil.boot_time()

    def render(self):
        uptime_s = time.time() - self.boot_time
        d = datetime(1, 1, 1) + timedelta(seconds=uptime_s)
        right = [f"up {d.day - 1}d, {d.hour}:{d.minute:02d}h"]

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
