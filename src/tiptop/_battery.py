import psutil
from rich import box
from rich.panel import Panel
from textual.widget import Widget

from .braille_stream import BrailleStream


class Battery(Widget):
    def on_mount(self):
        self.is_first_render = True
        self.bat_stream = BrailleStream(40, 4, 0.0, 100.0)
        # update frequency: 1 min
        self.set_interval(60.0, self.collect_data)

    def collect_data(self):
        bat = psutil.sensors_battery()

        self.bat_stream.add_value(bat.percent)

        battery_graph = "[yellow]" + "\n".join(self.bat_stream.graph) + "[/]\n"

        if bat.power_plugged:
            status = "charging"
        else:
            mm = bat.secsleft // 60
            hh, mm = divmod(mm, 60)
            time_left_str = []
            if hh > 0:
                time_left_str.append(f"{hh}h")
            if mm > 0:
                time_left_str.append(f"{mm}min")
            status = " ".join(time_left_str) + " left"

        title = f"battery - {self.bat_stream.values[-1]:.1f}% - {status}"
        if bat.percent < 15 and not bat.power_plugged:
            title = "[red reverse bold]" + title + "[/]"

        self.panel = Panel(
            battery_graph,
            title=title,
            title_align="left",
            border_style="yellow",
            box=box.SQUARE,
        )
        self.refresh()

    def render(self) -> Panel:
        if self.is_first_render:
            self.collect_data()
            self.is_first_render = False
        return self.panel

    async def on_resize(self, event):
        self.bat_stream.reset_width(event.width - 4)
        self.bat_stream.reset_height(event.height - 2)
