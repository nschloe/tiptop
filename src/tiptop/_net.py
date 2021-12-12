from __future__ import annotations

import socket

import psutil
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

from ._helpers import sizeof_fmt
from .braille_stream import BrailleStream


class Net(Widget):
    def __init__(self, interface: str | None = None):
        if interface is None:
            # try to find non-lo and non-docker interface that is up
            stats = psutil.net_if_stats()
            score_dict = {}
            for name, stats in stats.items():
                if not stats.isup:
                    score_dict[name] = 0
                elif name.startswith("lo") or name.startswith("docker"):
                    # local or docker
                    score_dict[name] = 1
                elif name.startswith("fw"):
                    # firewire https://github.com/nschloe/tiptop/issues/45#issuecomment-991884364
                    score_dict[name] = 2
                else:
                    score_dict[name] = 3

            # Get key with max score
            # https://stackoverflow.com/a/280156/353337
            self.interface = max(score_dict, key=score_dict.get)
        else:
            self.interface = interface

        super().__init__()

    def on_mount(self):
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

    # would love to collect data upon each render(), but render is called too often
    # <https://github.com/willmcgugan/textual/issues/162>
    def collect_data(self):
        addrs = psutil.net_if_addrs()[self.interface]
        ipv4 = []
        for addr in addrs:
            # ipv4?
            if addr.family == socket.AF_INET:
                ipv4.append(addr.address + " / " + addr.netmask)
        ipv6 = []
        for addr in addrs:
            # ipv4?
            if addr.family == socket.AF_INET6:
                ipv6.append(addr.address)

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
            style="green",
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
            style="blue",
            width=20,
            box=box.SQUARE,
        )

        t = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        t.add_column("graph", no_wrap=True, ratio=1)
        t.add_column("box", no_wrap=True, width=down_box.width)

        t.add_row("[green]" + "\n".join(self.recv_stream.graph) + "[/]", down_box)
        t.add_row("[blue]" + "\n".join(self.sent_stream.graph) + "[/]", up_box)

        ipv4 = "\n      ".join(ipv4)
        ipv6 = "\n      ".join(ipv6)
        g = Group(t, f"[b]IPv4:[/] {ipv4}", f"[b]IPv6:[/] {ipv6}")

        self.content = Panel(
            g,
            title=f"net - {self.interface}",
            border_style="red",
            title_align="left",
            box=box.SQUARE,
        )

        self.refresh()

    def render(self):
        return self.content

    async def on_resize(self, event):
        self.sent_stream.reset_width(event.width - 25)
        self.recv_stream.reset_width(event.width - 25)
