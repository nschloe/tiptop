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

# def get_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     s.connect(("8.8.8.8", 80))
#     ip = s.getsockname()[0]
#     s.close()
#     return ip


def _autoselect_interface():
    """try to find non-lo and non-docker interface that is up"""
    stats = psutil.net_if_stats()
    score_dict = {}
    for name, stats in stats.items():
        if not stats.isup:
            score_dict[name] = 0
        elif (
            # On Unix, we have `lo`, on Windows `Loopback Pseudo-Interface k`
            # and `Local Area Connection k` (the latter is valid)
            name.startswith("lo")
            or name.lower().startswith("loopback")
            or name.lower().startswith("docker")
        ):
            score_dict[name] = 1
        elif name.lower().startswith("fw") or name.lower().startswith("Bluetooth"):
            # firewire <https://github.com/nschloe/tiptop/issues/45#issuecomment-991884364>
            # or bluetooth
            score_dict[name] = 2
        else:
            score_dict[name] = 3

    # Get key with max score
    # https://stackoverflow.com/a/280156/353337
    return max(score_dict, key=score_dict.get)


class Net(Widget):
    def __init__(self, interface: str | None = None):
        self.interface = _autoselect_interface() if interface is None else interface
        super().__init__()

    def on_mount(self):
        self.panel = Panel(
            "",
            title=f"net - {self.interface}",
            border_style="red",
            title_align="left",
            box=box.SQUARE,
        )
        self.down_box = Panel(
            "",
            title="▼ down",
            title_align="left",
            style="green",
            width=20,
            box=box.SQUARE,
        )
        self.up_box = Panel(
            "",
            title="▲ up",
            title_align="left",
            style="blue",
            width=20,
            box=box.SQUARE,
        )

        self.last_net = None
        self.max_recv_bytes_s = 0
        self.max_recv_bytes_s_str = ""
        self.max_sent_bytes_s = 0
        self.max_sent_bytes_s_str = ""

        self.recv_stream = BrailleStream(20, 5, 0.0, 1.0e6)
        self.sent_stream = BrailleStream(20, 5, 0.0, 1.0e6, flipud=True)

        self.refresh_ips()
        self.refresh_panel()

        self.interval_s = 2.0
        self.set_interval(self.interval_s, self.refresh_panel)
        self.set_interval(60.0, self.refresh_ips)

    def refresh_ips(self):
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
        self.ipv4 = "\n      ".join(ipv4)
        self.ipv6 = "\n      ".join(ipv6)

    # would love to collect data upon each render(), but render is called too often
    # <https://github.com/willmcgugan/textual/issues/162>
    def refresh_panel(self):
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

        self.down_box.renderable = "\n".join(
            [
                f"{recv_bytes_s_string}",
                f"max   {self.max_recv_bytes_s_str}",
                f"total {total_recv_string}",
            ]
        )
        self.up_box.renderable = "\n".join(
            [
                f"{sent_bytes_s_string}",
                f"max   {self.max_sent_bytes_s_str}",
                f"total {total_sent_string}",
            ]
        )

        t = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        t.add_column("graph", no_wrap=True, ratio=1)
        t.add_column("box", no_wrap=True, width=self.down_box.width)

        t.add_row("[green]" + "\n".join(self.recv_stream.graph) + "[/]", self.down_box)
        t.add_row("[blue]" + "\n".join(self.sent_stream.graph) + "[/]", self.up_box)

        self.panel.renderable = Group(
            t, f"[b]IPv4:[/] {self.ipv4}", f"[b]IPv6:[/] {self.ipv6}"
        )

        self.refresh()

    def render(self):
        return self.panel

    async def on_resize(self, event):
        self.sent_stream.reset_width(event.width - 25)
        self.recv_stream.reset_width(event.width - 25)
