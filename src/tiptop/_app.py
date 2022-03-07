from __future__ import annotations

import argparse
from sys import version_info

import psutil
from textual.app import App

from .__about__ import __version__
from ._battery import Battery
from ._cpu import CPU
from ._disk import Disk
from ._info import InfoLine
from ._mem import Mem
from ._net import Net
from ._procs_list import ProcsList

# class TiptopApp(App):
#     async def on_mount(self) -> None:
#         await self.view.dock(InfoLine(), edge="top", size=1, name="info")
#         await self.view.dock(CPU(), edge="top", size=14, name="cpu")
#         await self.view.dock(ProcsList(), edge="right", size=70, name="proc")
#         await self.view.dock(Mem(), edge="top", size=20, name="mem")
#         await self.view.dock(Net(), edge="bottom", name="net")
#
#     async def on_load(self, _):
#         await self.bind("i", "view.toggle('info')", "Toggle info")
#         await self.bind("c", "view.toggle('cpu')", "Toggle cpu")
#         await self.bind("m", "view.toggle('mem')", "Toggle mem")
#         await self.bind("n", "view.toggle('net')", "Toggle net")
#         await self.bind("p", "view.toggle('proc')", "Toggle proc")
#         await self.bind("q", "quit", "quit")


def run(argv=None):
    parser = argparse.ArgumentParser(
        description="Command-line system monitor.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=_get_version_text(),
        help="display version information",
    )

    parser.add_argument(
        "--log",
        "-l",
        type=str,
        default=None,
        help="debug log file",
    )

    parser.add_argument(
        "--net",
        "-n",
        type=str,
        default=None,
        help="network interface to display (default: auto)",
    )

    args = parser.parse_args(argv)

    # with a grid
    class TiptopApp(App):
        async def on_mount(self) -> None:
            grid = await self.view.dock_grid(edge="left")

            # 34/55: approx golden ratio. See
            # <https://gist.github.com/nschloe/ab6c3c90b4a6bc02c40405803fa8fa35>
            # for the error.
            grid.add_column(fraction=55, name="left")
            grid.add_column(fraction=34, name="right")

            if psutil.sensors_battery() is None:
                grid.add_row(size=1, name="topline")
                grid.add_row(fraction=1, name="top")
                grid.add_row(fraction=1, name="center")
                grid.add_row(fraction=1, name="bottom")
                grid.add_areas(
                    area0="left-start|right-end,topline",
                    area1="left-start|right-end,top",
                    area2a="left,center",
                    area2b="left,bottom",
                    area3="right,center-start|bottom-end",
                )
                grid.place(
                    area0=InfoLine(),
                    area1=CPU(),
                    area2a=Mem(),
                    area2b=Net(args.net),
                    area3=ProcsList(),
                )
            else:
                grid.add_row(size=1, name="r0")
                grid.add_row(fraction=17, name="r1")
                grid.add_row(fraction=4, name="r2")
                grid.add_row(fraction=15, name="r3")
                grid.add_row(fraction=15, name="r4")
                grid.add_areas(
                    area0="left-start|right-end,r0",
                    area1="left,r1",
                    area2a="right,r1",
                    area2b="right,r2",
                    area2c="right,r3",
                    area2d="right,r4",
                    area3="left,r2-start|r4-end",
                )
                grid.place(
                    area0=InfoLine(),
                    area1=CPU(),
                    area2a=Mem(),
                    area2b=Battery(),
                    area2c=Disk(),
                    area2d=Net(args.net),
                    area3=ProcsList(),
                )

        async def on_load(self, _):
            await self.bind("q", "quit", "quit")

    TiptopApp.run(log=args.log)


def _get_version_text():
    python_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    return "\n".join(
        [
            f"tiptop {__version__} [Python {python_version}]",
            "Copyright (c) 2021-2022 Nico Schlömer",
        ]
    )
