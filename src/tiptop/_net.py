import socket

import psutil
from rich import box
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from .braille_stream import BrailleStream
from ._helpers import sizeof_fmt


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
