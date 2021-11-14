from textual.app import App

from ._cpu import CPU
from ._info import InfoLine
from ._mem import Mem
from ._net import Net
from ._procs_list import ProcsList


def run():
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

    # with a grid
    class TiptopApp(App):
        async def on_mount(self) -> None:
            grid = await self.view.dock_grid(edge="left")

            # 34/55: approx golden ratio. See
            # <https://gist.github.com/nschloe/ab6c3c90b4a6bc02c40405803fa8fa35>
            # for the error.
            grid.add_column(fraction=34, name="left")
            grid.add_column(fraction=55, name="right")

            grid.add_row(size=1, name="topline")
            grid.add_row(fraction=1, name="top")
            grid.add_row(fraction=1, name="center")
            grid.add_row(fraction=1, name="bottom")

            grid.add_areas(
                area0="left-start|right-end,topline",
                area1="left-start|right-end,top",
                area2="left,center",
                area3="left,bottom",
                area4="right,center-start|bottom-end",
            )

            grid.place(
                area0=InfoLine(),
                area1=CPU(),
                area2=Mem(),
                area3=Net(),
                area4=ProcsList(),
            )

        async def on_load(self, _):
            await self.bind("q", "quit", "quit")

    TiptopApp.run()
