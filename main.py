import flet as ft
import getpass
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class Mapper:
    def __init__(self):
        self._keys = []
        self._values = []

    def put(self, key, value):
        if key in self._keys:
            idx = self._keys.index(key)
            self._values[idx] = value
        else:
            self._keys.append(key)
            self._values.append(value)

    def get(self, key):
        if key in self._keys:
            return self._values[self._keys.index(key)]
        return None


class Codecs:
    def __init__(self, name: str, complexity: int):
        self._name = name
        self._complexity = complexity

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def complexity(self):
        return self._complexity

    @complexity.setter
    def complexity(self, value):
        self._complexity = value

    def __eq__(self, other):
        return self.complexity == other.complexity

    def __lt__(self, other):
        return self.complexity < other.complexity

    def __gt__(self, other):
        return self.complexity > other.complexity

    def __len__(self):
        return self.complexity

    def __repr__(self):
        return f"<Codecs: {self.name}>"

    def __str__(self):
        return f"{self.name} (сложность: {self.complexity})"

class BaseTask(ABC):
    def __init__(self, input_path: str, target_format: str):
        self._input_path = input_path
        self._target_format = target_format

    @property
    def input_path(self):
        return self._input_path

    @input_path.setter
    def input_path(self, value):
        self._input_path = value

    @property
    def target_format(self):
        return self._target_format

    @target_format.setter
    def target_format(self, value):
        self._target_format = value

    @abstractmethod
    def generate_command(self) -> str:
        pass

class Video(BaseTask):
    def __init__(self, input_path: str, target_format: str, codec: Codecs):
        super().__init__(input_path, target_format)
        self.codec = codec

    def generate_command(self) -> str:
        p = Path(self.input_path)
        out_path = p.with_name(f"{p.stem}_converted.{self.target_format}")
        return f'ffmpeg -i "{self.input_path}" -c:v {self.codec.name} -c:a aac "{out_path}"'

class Audio(BaseTask):
    def generate_command(self) -> str:
        p = Path(self.input_path)
        out_path = p.with_name(f"{p.stem}_converted.{self.target_format}")
        return f'ffmpeg -i "{self.input_path}" -b:a 192k "{out_path}"'

class Title(ft.Text):
    def __init__(self, value: str):
        super().__init__()
        self.value = value
        self.size = 26
        self.weight = ft.FontWeight.BOLD
        self.color = ft.Colors.BLUE_800
        self.text_align = ft.TextAlign.CENTER

class Pbutton(ft.Container):  
    def __init__(self, text: str, on_click_action):
        super().__init__()
        self.content = ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.bgcolor = ft.Colors.GREY_600
        self.on_click = on_click_action
        self.alignment = ft.Alignment.CENTER

class History(ft.Container):
    def __init__(self, text: str):
        super().__init__()
        self.content = ft.Text(text, size=14, selectable=True, color=ft.Colors.WHITE)
        self.padding = 10
        self.bgcolor = ft.Colors.GREY_700
        #self.bgcolor = ft.Colors.GREEN_50        

class FfmpegApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.time_in = datetime.now()
        self.os_username = getpass.getuser()
        
        self.page.title = "FFmpeg Generator"
        #self.bgcolor = ft.Colors.BLACK
        self.page.bgcolor = ft.Colors.GREY_900
        self.page.window.width = 650
        self.page.window.height = 750
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.padding = 30
        
        self.codecs = [
            Codecs("libx264", 50),
            Codecs("libx265", 80),
            Codecs("mpeg4", 20),
            Codecs("vp9", 75),
            Codecs("copy", 10)
        ]
        self.codecs.sort()

        self.format_map = Mapper()
        self.format_map.put("mp4", "video")
        self.format_map.put("mkv", "video")
        self.format_map.put("avi", "video")
        self.format_map.put("mp3", "audio")
        self.format_map.put("wav", "audio")

        self.path_field = ft.TextField(label="полный путь к файлу", width=500,)
        
        #self.format_box = ft.Dropdown(
        #    label="выходной формат",
        #    width=500,
        #    options=[
        #        ft.dropdown.Option("mp4"), ft.dropdown.Option("mkv"), ft.dropdown.Option("avi"),
        #        ft.dropdown.Option("mp3"), ft.dropdown.Option("wav")
        #    ],
        #    on_select=self.on_format_change
        #)

        self.format_box = ft.Dropdown(
            label="выходной формат",
            width=240,
            options=[
                ft.dropdown.Option("mp4"), ft.dropdown.Option("mkv"), ft.dropdown.Option("avi"),
                ft.dropdown.Option("mp3"), ft.dropdown.Option("wav")
            ],
            on_select=self.on_format_change
        )

        self.codec_box = ft.Dropdown(
            label="кодек",
            width=240,
            options=[ft.dropdown.Option(c.name) for c in self.codecs],
            #visible=False
        )

        self.history_list = ft.ListView(height=200, spacing=10)

        self.page.window.prevent_close = True
        self.page.window.on_event = self.on_window_event

        main_column = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            width=500,
            controls=[
                Title("FFmpeg Generator"),
                ft.Text(f"{self.os_username}", color=ft.Colors.GREY_700),
                ft.Divider(),
                self.path_field,
                #self.format_box,
                #self.codec_box,
                ft.Row(
                    controls=[self.format_box, self.codec_box],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    width=500
                ),
                Pbutton("сгенерировать команду", self.generate_command),
                ft.Divider(),
                ft.Text("история скоманд:", weight=ft.FontWeight.BOLD),
                self.history_list
            ]
        )
        self.page.add(main_column)

    def on_format_change(self, e):
        selected_fmt = self.format_box.value
        if not selected_fmt: return
        
        media_type = self.format_map.get(selected_fmt)
        
        if media_type == "video":
            self.codec_box.disabled = False
            if not self.codec_box.value:
                self.codec_box.value = "libx264"
        else:
            self.codec_box.disabled = True
            self.codec_box.value = None
            
        self.page.update()

    def generate_command(self, e):
        path = self.path_field.value
        fmt = self.format_box.value

        if not path:
            self.history_list.controls.insert(0, History("укажите путь"))
            self.page.update()
            return

        if not fmt:
                    self.history_list.controls.insert(0, History("укажите формат"))
                    self.page.update()
                    return

        media_type = self.format_map.get(fmt)
        
        if media_type == "video":
            codec_name = self.codec_box.value or "libx264"
            selected_codec = next((c for c in self.codecs if c.name == codec_name), self.codecs[0])
            task = Video(path, fmt, selected_codec)
        else:
            task = Audio(path, fmt)

        command = task.generate_command()
        
        self.history_list.controls.insert(0, History(command))
        self.page.update()

    @staticmethod
    def format_time(dt: datetime) -> str:
        return dt.strftime("%d.%m.%Y %H:%M:%S")

    async def on_window_event(self, e):
        if getattr(e, "type", None) == ft.WindowEventType.CLOSE or e.data == "close":
            time_out = datetime.now()
            login = self.os_username
            
            str_in = FfmpegApp.format_time(self.time_in)
            str_out = FfmpegApp.format_time(time_out)

            #report_content = (
            #    #f"+-------------------------------------------------------------+\n"
            #    #f"| login | time_in | tiem_out |\n"
            #    #f"|-----------------|--------------------|--------------------|\n"
            #    f"+-------------------------------------------------------------+\n"
            #    f"| {login[:15]:<15} | {str_in:<18} | {str_out:<18} |\n"
            #    f"+-------------------------------------------------------------+\n"
            #)
            report_content = (
                f"+---------------------------------------------------------------+\n"
                f"| {'login':<15} | {'time_in':<20} | {'time_out':<20} |\n"
                f"|-----------------|----------------------|----------------------|\n"
                f"| {login[:15]:<15} | {str_in:<20} | {str_out:<20} |\n"
                f"+---------------------------------------------------------------+\n"
            )

            with open("report.txt", "w", encoding="utf-8") as file:
                file.write(report_content)
                
            await self.page.window.destroy()

def main(page: ft.Page):
    app = FfmpegApp(page)

if __name__ == "__main__":
    ft.run(main)