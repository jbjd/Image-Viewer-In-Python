from tkinter import Canvas, Event, Tk
from typing import Final

from PIL.ImageTk import PhotoImage

from constants import TEXT_RGB, ButtonName, TkTags
from ui.bases import ButtonBase


class CustomCanvas(Canvas):  # pylint: disable=too-many-ancestors
    """Custom version of tkinter's canvas to support internal methods"""

    __slots__ = (
        "button_name_to_object",
        "drag_start_x",
        "drag_start_y",
        "file_name_text_id",
        "image_display_id",
        "screen_width",
        "screen_height",
        "topbar",
    )

    def __init__(self, master: Tk) -> None:
        super().__init__(master, bg="black", highlightthickness=0)
        self.pack(anchor="nw", fill="both", expand=1)

        master.update()  # updates winfo width and height to the current size
        self.button_name_to_object: dict[ButtonName, ButtonBase] = {}
        self.file_name_text_id: int = -1
        self.image_display_id: int = -1
        self.screen_width: int = master.winfo_width()
        self.screen_height: int = master.winfo_height()
        self.drag_start_x: int
        self.drag_start_y: int
        self.topbar: PhotoImage

        self.create_rectangle(
            0,
            0,
            self.screen_width,
            self.screen_height,
            fill="black",
            tags=TkTags.BACKGROUND,
        )

        self.bind("<ButtonPress-3>", self._move_from)
        self.bind("<B3-Motion>", self._move_to)

    def _move_from(self, event: Event) -> None:
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _move_to(self, event: Event) -> None:
        drag_x: int = event.x - self.drag_start_x
        drag_y: int = event.y - self.drag_start_y
        self.drag_start_x += drag_x
        self.drag_start_y += drag_y

        bbox: tuple[int, int, int, int] = self.bbox(self.image_display_id)
        # Keep in bounds horizontally
        if drag_x < 0 and bbox[2] + drag_x <= 0:
            drag_x = -bbox[2]
        elif drag_x > 0 and bbox[0] + drag_x >= self.screen_width:
            drag_x = self.screen_width - bbox[0]

        # Keep in bounds vertically
        if drag_y < 0 and bbox[3] + drag_y <= 0:
            drag_y = -bbox[3]
        elif drag_y > 0 and bbox[1] + drag_y >= self.screen_height:
            drag_y = self.screen_height - bbox[1]

        self.move(self.image_display_id, drag_x, drag_y)

    def create_button(
        self,
        button_object: ButtonBase,
        name: ButtonName,
        x_offset: int,
        y_offset: int,
        image: PhotoImage,
    ) -> int:
        id: int = self.create_image(
            x_offset,
            y_offset,
            image=image,
            anchor="nw",
            tag=TkTags.TOPBAR,
            state="hidden",
        )

        self.button_name_to_object[name] = button_object

        return id

    def create_topbar(self, topbar_img: PhotoImage) -> None:
        """Creates the topbar and stores it"""
        self.topbar = topbar_img  # save from garbage collector
        self.create_image(
            0, 0, image=topbar_img, anchor="nw", tag=TkTags.TOPBAR, state="hidden"
        )

    def create_name_text(self, x: int, y: int, font: str) -> None:
        """Creates text object used to display file name"""
        self.file_name_text_id = self.create_text(
            x,
            y,
            fill=TEXT_RGB,
            anchor="w",
            font=font,
            tags=TkTags.TOPBAR,
        )

    def update_image_display(self, new_image: PhotoImage) -> None:
        """Puts a new image on screen"""
        self.delete(self.image_display_id)

        self.image_display_id = self.create_image(
            self.screen_width >> 1,
            self.screen_height >> 1,
            anchor="center",
            tag=TkTags.BACKGROUND,
            image=new_image,
        )
        self.tag_raise(TkTags.TOPBAR)
        self.master.update_idletasks()

    def update_existing_image_display(self, new_image: PhotoImage) -> None:
        """Updates existing image on screen with a new PhotoImage"""
        self.itemconfig(self.image_display_id, image=new_image)
        self.master.update_idletasks()

    def update_file_name(self, new_name: str) -> int:
        """Updates file name. Returns width of new name"""
        self.itemconfigure(self.file_name_text_id, text=self._clean_long_name(new_name))
        return self.bbox(self.file_name_text_id)[2]

    @staticmethod
    def _clean_long_name(image_name: str) -> str:
        """Takes a name and returns a shortened version if its too long"""
        end_index: int = image_name.rfind(".")
        MAX: Final[int] = 40
        if end_index < MAX:
            return image_name
        return f"{image_name[:MAX-2]}(…){image_name[end_index:]}"

    def is_widget_visible(self, tag_or_id: str | int) -> bool:
        """Returns bool of if provided tag/id is visible"""
        return self.itemcget(tag_or_id, "state") != "hidden"

    def get_button_id(self, name: ButtonName) -> int:
        return self.button_name_to_object[name].id

    def mock_button_click(self, name: ButtonName) -> None:
        """Triggers on click event of button programatically
        passing None as event"""
        button: ButtonBase = self.button_name_to_object[name]
        button.on_click(None)
        button.on_leave(None)  # Don't make button look hovered by mouse
