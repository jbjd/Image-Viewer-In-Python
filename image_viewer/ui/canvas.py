from tkinter import Canvas, Event, Tk
from typing import Final

from PIL.ImageTk import PhotoImage

from constants import TEXT_RGB, TkTags


class CustomCanvas(Canvas):  # pylint: disable=too-many-ancestors
    """Custom version of tkinter's canvas to support internal methods"""

    __slots__ = (
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

    def get_bbox_to_cull_offscreen_image_parts(
        self, true_dimensions: tuple[int, int]
    ) -> tuple[float, float, float, float]:
        """Returns bbox of image display only including visible parts"""
        canvas_x1, canvas_y1, canvas_x2, canvas_y2 = self.bbox(self.image_display_id)
        true_width, true_height = true_dimensions
        width_on_canvas, height_on_canvas = canvas_x2 - canvas_x1, canvas_y2 - canvas_y1

        image_center_x = canvas_x1 + (width_on_canvas / 2)
        image_center_y = canvas_y1 + (height_on_canvas / 2)

        # Chop off invisisble parts
        canvas_x1 = max(canvas_x1, 0)
        canvas_y1 = max(canvas_y1, 0)

        # canvas canvas coords on 0,0
        canvas_x1 -= image_center_x
        canvas_y1 -= image_center_y
        canvas_x2 -= image_center_x
        canvas_y2 -= image_center_y

        canvas_width_ratio = true_width / width_on_canvas
        canvas_height_ratio = true_height / height_on_canvas

        canvas_x1 *= canvas_width_ratio
        canvas_y1 *= canvas_height_ratio
        canvas_x2 *= canvas_width_ratio
        canvas_y2 *= canvas_height_ratio

        # TODO: Centering is incorrect, chopping left/top without chopping right/bottom
        # When image is centered. Should be chopping all sides equally
        canvas_x1 += true_width / 2
        canvas_y1 += true_height / 2
        canvas_x2 += true_width / 2
        canvas_y2 += true_height / 2

        return (canvas_x1, canvas_y1, canvas_x2, canvas_y2)
